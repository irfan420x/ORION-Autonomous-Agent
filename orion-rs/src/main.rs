use serde::{Deserialize, Serialize};
use std::env;
use std::path::Path;
use std::sync::mpsc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use sysinfo::{CpuRefreshKind, Disks, MemoryRefreshKind, RefreshKind, System};
use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};

#[derive(Serialize, Deserialize, Debug)]
struct ProcessInfo {
    pid: u32,
    name: String,
    cpu_usage: f32,
    memory_bytes: u64,
    memory_percent: f32,
    status: String,
    parent_pid: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug)]
struct SystemSnapshot {
    timestamp: u64,
    cpu_count: usize,
    cpu_usage_per_core: Vec<f32>,
    total_memory_mb: u64,
    used_memory_mb: u64,
    memory_percent: f32,
    total_disk_mb: u64,
    used_disk_mb: u64,
    disk_percent: f32,
    process_count: usize,
    top_processes: Vec<ProcessInfo>,
    uptime_seconds: u64,
}

#[derive(Serialize, Deserialize, Debug)]
struct FileEvent {
    timestamp: u64,
    kind: String,
    paths: Vec<String>,
}

fn now_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn status_str(s: sysinfo::ProcessStatus) -> String {
    match s {
        sysinfo::ProcessStatus::Run => "running".into(),
        sysinfo::ProcessStatus::Sleep => "sleeping".into(),
        sysinfo::ProcessStatus::Stop => "stopped".into(),
        sysinfo::ProcessStatus::Zombie => "zombie".into(),
        sysinfo::ProcessStatus::Idle => "idle".into(),
        sysinfo::ProcessStatus::Tracing => "tracing".into(),
        sysinfo::ProcessStatus::UninterruptibleDiskSleep => "disk_sleep".into(),
        sysinfo::ProcessStatus::Wakekill => "wakekill".into(),
        sysinfo::ProcessStatus::Waking => "waking".into(),
        sysinfo::ProcessStatus::Parked => "parked".into(),
        _ => "unknown".into(),
    }
}

fn scan_processes(sys: &System, limit: usize) -> Vec<ProcessInfo> {
    let mut procs: Vec<ProcessInfo> = sys
        .processes()
        .iter()
        .map(|(pid, proc_info)| ProcessInfo {
            pid: pid.as_u32(),
            name: proc_info.name().to_string(),
            cpu_usage: proc_info.cpu_usage(),
            memory_bytes: proc_info.memory(),
            memory_percent: proc_info.memory() as f32 / sys.total_memory() as f32 * 100.0,
            status: status_str(proc_info.status()),
            parent_pid: proc_info.parent().map(|p| p.as_u32()),
        })
        .collect();

    procs.sort_by(|a, b| {
        b.cpu_usage
            .partial_cmp(&a.cpu_usage)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    procs.truncate(limit);
    procs
}

fn system_snapshot(sys: &System, top_n: usize) -> SystemSnapshot {
    let cpu_usage = sys.cpus().iter().map(|c| c.cpu_usage()).collect::<Vec<_>>();

    let disks = Disks::new_with_refreshed_list();
    let (total_disk, used_disk) = disks.list().iter().fold((0u64, 0u64), |(t, u), d| {
        (
            t + d.total_space() / 1024 / 1024,
            u + (d.total_space() - d.available_space()) / 1024 / 1024,
        )
    });

    SystemSnapshot {
        timestamp: now_millis(),
        cpu_count: sys.cpus().len(),
        cpu_usage_per_core: cpu_usage,
        total_memory_mb: sys.total_memory() / 1024 / 1024,
        used_memory_mb: sys.used_memory() / 1024 / 1024,
        memory_percent: sys.used_memory() as f32 / sys.total_memory() as f32 * 100.0,
        total_disk_mb: total_disk,
        used_disk_mb: used_disk,
        disk_percent: if total_disk > 0 {
            used_disk as f32 / total_disk as f32 * 100.0
        } else {
            0.0
        },
        process_count: sys.processes().len(),
        top_processes: scan_processes(sys, top_n),
        uptime_seconds: System::uptime(),
    }
}

fn watch_directory(path: &str, duration_secs: u64) -> Vec<FileEvent> {
    let (tx, rx) = mpsc::channel::<notify::Result<Event>>();
    let mut watcher =
        RecommendedWatcher::new(tx, Config::default()).expect("Failed to create watcher");

    watcher
        .watch(Path::new(path), RecursiveMode::Recursive)
        .expect("Failed to watch path");

    let start = Instant::now();
    let timeout = Duration::from_secs(duration_secs);
    let mut events = Vec::new();

    while start.elapsed() < timeout {
        match rx.recv_timeout(Duration::from_millis(500)) {
            Ok(Ok(event)) => {
                let kind = match event.kind {
                    EventKind::Create(_) => "created",
                    EventKind::Modify(_) => "modified",
                    EventKind::Remove(_) => "removed",
                    EventKind::Access(_) => "accessed",
                    _ => "other",
                };
                events.push(FileEvent {
                    timestamp: now_millis(),
                    kind: kind.to_string(),
                    paths: event
                        .paths
                        .iter()
                        .map(|p| p.display().to_string())
                        .collect(),
                });
            }
            _ => {}
        }
    }

    events
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|s| s.as_str()).unwrap_or("snapshot");

    let mut sys = System::new_with_specifics(
        RefreshKind::new()
            .with_cpu(CpuRefreshKind::new().with_cpu_usage())
            .with_memory(MemoryRefreshKind::new().with_ram()),
    );

    match command {
        "snapshot" => {
            std::thread::sleep(Duration::from_millis(200));
            sys.refresh_all();
            let snap = system_snapshot(&sys, 20);
            println!(
                "{}",
                serde_json::to_string_pretty(&snap).unwrap()
            );
        }
        "processes" => {
            std::thread::sleep(Duration::from_millis(200));
            sys.refresh_all();
            let top_n = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(20);
            let procs = scan_processes(&sys, top_n);
            println!("{}", serde_json::to_string_pretty(&procs).unwrap());
        }
        "watch" => {
            let path = args.get(2).map(|s| s.as_str()).unwrap_or(".");
            let secs = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(10);
            eprintln!("Watching {} for {} seconds...", path, secs);
            let events = watch_directory(path, secs);
            println!("{}", serde_json::to_string_pretty(&events).unwrap());
        }
        "health" => {
            std::thread::sleep(Duration::from_millis(200));
            sys.refresh_all();
            let snap = system_snapshot(&sys, 5);
            let status = if snap.memory_percent > 90.0 || snap.disk_percent > 95.0 {
                "CRITICAL"
            } else if snap.memory_percent > 75.0 || snap.disk_percent > 85.0 {
                "DEGRADED"
            } else {
                "HEALTHY"
            };
            println!(
                "{}",
                serde_json::json!({
                    "status": status,
                    "cpu_cores": snap.cpu_count,
                    "memory_percent": snap.memory_percent,
                    "disk_percent": snap.disk_percent,
                    "process_count": snap.process_count,
                    "uptime_seconds": snap.uptime_seconds,
                })
            );
        }
        _ => {
            eprintln!("orion-rs: Rust performance layer for ORION");
            eprintln!();
            eprintln!("Usage: orion-rs <command> [args]");
            eprintln!();
            eprintln!("Commands:");
            eprintln!("  snapshot          Full system snapshot");
            eprintln!("  processes [N]     Top N processes by CPU");
            eprintln!("  watch <path> [s]  Watch directory for changes");
            eprintln!("  health            Quick health check");
        }
    }
}
