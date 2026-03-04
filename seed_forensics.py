#!/usr/bin/env python3
"""
================================================================================
  DIGITAL FORENSICS KNOWLEDGE SEEDER — Diamond Brain
================================================================================
  Seeds the Diamond Brain with comprehensive digital forensics knowledge.
  Covers tools, concepts, artifacts, methodologies, and CLI commands.

  Usage:
      python seed_forensics.py              # Seed all forensics knowledge
      python seed_forensics.py --dry-run    # Preview without writing
      python seed_forensics.py --stats      # Show post-seed statistics

  Sources: NIST SP 800-86, SANS DFIR, RFC 3227, Volatility Foundation,
           MITRE ATT&CK, vendor documentation (2025-2026 current).
================================================================================
"""

import sys
from pathlib import Path

# Ensure brain module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brain.diamond_brain import DiamondBrain


# ============================================================================
# FORENSICS KNOWLEDGE BASE
# ============================================================================
# Each entry: (category, fact, confidence, severity)
# Confidence: 85-100 based on source reliability and currency
# Severity: HIGH = must-know, MEDIUM = important, LOW = good-to-know
# ============================================================================

FORENSICS_KNOWLEDGE = [

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Disk/Image Forensics
    # ========================================================================
    (
        "forensics-tools-disk",
        "Autopsy is the premier open-source digital forensics platform built on The Sleuth Kit (TSK). Provides GUI-based disk image analysis, keyword search, timeline generation, hash filtering, and module-based extensibility. Supports E01, raw/dd, and VMDK image formats. Industry standard for law enforcement and academic forensics.",
        97, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "The Sleuth Kit (TSK) is a C library and collection of CLI tools for analyzing disk images and file systems (NTFS, FAT, ext2/3/4, HFS+, APFS, UFS). Core commands: fls (list files), icat (extract by inode), mmls (partition layout), fsstat (filesystem details). Foundation for Autopsy and many commercial tools.",
        96, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "EnCase Forensic (OpenText) is an industry-standard commercial forensic suite used by law enforcement and enterprises worldwide. Supports evidence acquisition, analysis, and reporting with court-accepted EnCase Evidence File Format (.E01). Features EnScript automation language for custom analysis workflows.",
        95, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "Forensic Toolkit (FTK) by Exterro provides enterprise-grade disk forensics with distributed processing, index-based searching, and Known File Filter (KFF). FTK Imager is a free standalone tool widely used for forensic imaging and evidence preview. Supports E01, AFF, SMART, and raw formats.",
        94, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "SIFT Workstation (SANS Investigative Forensics Toolkit) is a free Ubuntu-based forensic distribution maintained by SANS. Pre-loaded with 200+ forensic tools including log2timeline/plaso, Volatility, Autopsy, RegRipper, and bulk_extractor. Standard platform for SANS DFIR training and real-world investigations.",
        95, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "dc3dd and dcfldd are forensic-enhanced versions of the Unix dd command. dcfldd (DoD Computer Forensics Lab) adds on-the-fly hashing (MD5/SHA-256), split output, pattern wiping, and progress reporting. dc3dd adds similar features with a focus on forensic imaging best practices. Both produce court-admissible forensic images.",
        93, "HIGH"
    ),
    (
        "forensics-tools-disk",
        "Guymager is a free forensic imaging tool for Linux with a Qt GUI. Supports dd/raw, EWF/E01, and AFF formats with on-the-fly hashing. Known for fast multi-threaded acquisition and detailed log generation. Default imager in many Linux forensic distributions including SIFT and CAINE.",
        88, "MEDIUM"
    ),
    (
        "forensics-tools-disk",
        "X-Ways Forensics is a German-engineered commercial forensic tool known for extreme speed and low resource usage. Features include simultaneous searching, file header signature analysis, registry examination, and integrated disk cloning. Favored by European law enforcement agencies.",
        90, "MEDIUM"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Memory Forensics
    # ========================================================================
    (
        "forensics-tools-memory",
        "Volatility 3 (Python 3) is the dominant open-source memory forensics framework (2025-2026). Uses a modular layered architecture: memory layers, symbol tables, and object templates. Supports Windows, Linux, and macOS memory dumps. Volatility 2 is deprecated as of the Feature Parity release. Current version: 2.27+.",
        98, "HIGH"
    ),
    (
        "forensics-tools-memory",
        "Key Volatility 3 Windows plugins: windows.pslist (process listing), windows.psscan (hidden process detection), windows.netscan (network connections), windows.cmdline (command lines), windows.filescan (file objects), windows.dlllist (loaded DLLs), windows.malfind (injected code detection), windows.hashdump (password hashes).",
        97, "HIGH"
    ),
    (
        "forensics-tools-memory",
        "Key Volatility 3 Linux plugins: linux.pslist, linux.pstree, linux.bash (bash history from memory), linux.lsmod (loaded kernel modules), linux.proc.Maps, linux.sockstat (socket statistics), linux.check_syscall (syscall table hooks), linux.tty_check (TTY hijacking detection). Over 40 Linux-specific plugins available.",
        95, "HIGH"
    ),
    (
        "forensics-tools-memory",
        "Volatility Workbench provides a GUI front-end for Volatility 3 (based on v2.27.0, February 2026). Available from OSForensics. Simplifies memory analysis for investigators who prefer visual interfaces over CLI. Supports all standard Volatility 3 plugins.",
        88, "MEDIUM"
    ),
    (
        "forensics-tools-memory",
        "Rekall was an advanced memory forensics framework forked from Volatility, developed by Google. It is now deprecated and no longer maintained. Investigators should migrate to Volatility 3 for active memory forensics work. Historical Rekall profiles may need conversion for Volatility 3 compatibility.",
        87, "MEDIUM"
    ),
    (
        "forensics-tools-memory",
        "Memory acquisition tools: WinPmem (Windows), LiME (Linux Memory Extractor kernel module), and osxpmem (macOS). DumpIt is a popular Windows memory capture tool that creates a raw memory dump with a single click. FTK Imager also supports memory capture. Always capture memory BEFORE disk imaging due to volatility.",
        95, "HIGH"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Network Forensics
    # ========================================================================
    (
        "forensics-tools-network",
        "Wireshark is the world's most widely used network protocol analyzer. Supports 3000+ protocols, live capture and offline PCAP analysis, display filters (e.g., 'tcp.port == 443'), follow TCP streams, decrypt SSL/TLS with session keys, and export objects (HTTP files, SMB transfers). Essential for packet-level forensic investigation.",
        98, "HIGH"
    ),
    (
        "forensics-tools-network",
        "Zeek (formerly Bro) is a network security monitoring framework that generates structured, high-fidelity transaction logs for HTTP, DNS, SSL, SMTP, FTP, and other protocols. Uses its own scripting language for custom analysis. Scales to enterprise-level traffic. Outputs JSON/TSV logs ideal for SIEM ingestion and threat hunting.",
        96, "HIGH"
    ),
    (
        "forensics-tools-network",
        "tcpdump is the standard CLI packet capture tool on Unix/Linux. Key flags: -i (interface), -w (write pcap), -r (read pcap), -n (no DNS resolution), -X (hex+ASCII dump), -c (packet count), -s 0 (full packet capture). BPF filter syntax for targeted capture. Essential for headless/remote forensic collection.",
        95, "HIGH"
    ),
    (
        "forensics-tools-network",
        "NetworkMiner is a passive network forensic analyzer that extracts files, images, credentials, and OS fingerprints from PCAP files. Available as free and professional editions. Useful for rapid triage of network captures. Supports reassembly of transferred files without requiring full protocol analysis.",
        88, "MEDIUM"
    ),
    (
        "forensics-tools-network",
        "Arkime (formerly Moloch) is a large-scale, open-source, full-packet-capture and search system. Stores indexed PCAP data with an Elasticsearch backend and web-based interface. Designed for continuous network monitoring with petabyte-scale retention. Integrates with Zeek, Suricata, and YARA for enriched analysis.",
        90, "HIGH"
    ),
    (
        "forensics-tools-network",
        "Suricata is a high-performance network IDS/IPS and network security monitoring engine. Supports rule-based detection (compatible with Snort rules), protocol identification, file extraction, and TLS/JA3 fingerprinting. Multi-threaded architecture for high-speed network forensic analysis.",
        91, "HIGH"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Mobile Forensics
    # ========================================================================
    (
        "forensics-tools-mobile",
        "Cellebrite UFED is the most widely used commercial mobile forensic tool, adopted by law enforcement and intelligence agencies globally. Supports data extraction from smartphones, drones, SIM cards, SD cards, GPS devices, and legacy phones. Capable of advanced extraction methods including physical, file system, and logical acquisition.",
        96, "HIGH"
    ),
    (
        "forensics-tools-mobile",
        "Magnet AXIOM provides unified forensic analysis across mobile, computer, cloud, and vehicle data. Strong artifact recovery with timeline reconstruction, link analysis, and AI-powered categorization. Can ingest extractions from Cellebrite UFED, GrayKey, MSAB XRY, and Oxygen Forensics. Industry best practice: use multiple tools for validation.",
        95, "HIGH"
    ),
    (
        "forensics-tools-mobile",
        "GrayKey (Grayshift) specializes in iOS and Android device unlocking and extraction. Can bypass screen locks and encryption on many device models. Used primarily by law enforcement. Pairs with Magnet AXIOM for analysis. Access is restricted to verified law enforcement agencies.",
        92, "HIGH"
    ),
    (
        "forensics-tools-mobile",
        "MSAB XRY is a commercial mobile forensic tool supporting physical, logical, and cloud extraction from 37,000+ device profiles. Features XRY Cloud for extracting cloud-synced data from Google, Apple, Facebook, and other services. Strong in feature phone and legacy device support.",
        90, "MEDIUM"
    ),
    (
        "forensics-tools-mobile",
        "Oxygen Forensic Detective supports extraction and analysis of mobile devices, cloud services, drones, and IoT devices. Features JetEngine for fast data processing, facial recognition, social graph analysis, and SQLite database viewer. Supports warrant-based cloud extraction from 80+ cloud services.",
        90, "MEDIUM"
    ),
    (
        "forensics-tools-mobile",
        "MVT (Mobile Verification Toolkit) by Amnesty International is an open-source tool for checking mobile devices for signs of spyware (notably Pegasus). Analyzes iOS backups/filesystem dumps and Android backups. Essential for targeted surveillance investigations and journalist/activist protection.",
        91, "HIGH"
    ),
    (
        "forensics-tools-mobile",
        "No single tool provides complete mobile forensic coverage. Best practice is to use a combination of tools based on device type, OS version, encryption state, and extraction requirements. Always validate findings across multiple tools before presenting in court.",
        93, "HIGH"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Log Analysis
    # ========================================================================
    (
        "forensics-tools-logs",
        "Splunk is the leading commercial SIEM/log analysis platform. Supports ingestion from virtually any data source, SPL (Search Processing Language) for querying, dashboards, alerting, and correlation rules. Common forensic queries target authentication failures, lateral movement, and data exfiltration patterns.",
        95, "HIGH"
    ),
    (
        "forensics-tools-logs",
        "Elastic Stack (ELK: Elasticsearch, Logstash, Kibana) is a widely-used open-source log analysis platform. Elasticsearch provides full-text indexing, Logstash handles ingestion/parsing, and Kibana provides visualization. Elastic Security adds SIEM capabilities with detection rules aligned to MITRE ATT&CK.",
        94, "HIGH"
    ),
    (
        "forensics-tools-logs",
        "Chainsaw is an open-source tool (2025) for rapidly hunting through Windows forensic artifacts including Event Logs, MFT, and Shimcache. Uses Sigma detection rules and custom Chainsaw rules. Written in Rust for high performance. Ideal for rapid triage during incident response.",
        92, "HIGH"
    ),
    (
        "forensics-tools-logs",
        "Hayabusa is a Windows Event Log fast forensics timeline generator and threat hunting tool created by Yamato Security (Japan). Uses Sigma rules for detection. Generates super timelines from EVTX files. Written in Rust for speed. Outputs CSV/JSON for further analysis.",
        90, "HIGH"
    ),
    (
        "forensics-tools-logs",
        "Plaso (log2timeline) is the standard super-timeline creation tool. Parses 100+ artifact types from disk images, mounted volumes, or individual files. Generates unified timelines in CSV, JSON, or Elasticsearch format. Critical for forensic timeline analysis and event correlation.",
        96, "HIGH"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Malware Analysis
    # ========================================================================
    (
        "forensics-tools-malware",
        "YARA is the pattern-matching engine for malware researchers. Rules define text/binary patterns with boolean logic to identify malware families. YARA-X (2025+) is a Rust rewrite providing 2-10x faster scanning. Command: yara -r rules.yar /path/to/scan (recursive). Integrated into most commercial AV and sandbox solutions.",
        97, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "Cuckoo Sandbox / CAPE Sandbox is the standard open-source automated malware analysis system. Executes malware in isolated VMs and logs file modifications, registry changes, network activity, and API calls. CAPE (Community Advanced Platform Emulator) extends Cuckoo with payload extraction and de-obfuscation for packed malware (Emotet, TrickBot).",
        95, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "FLOSS (FLARE Obfuscated String Solver) by Mandiant extracts and deobfuscates strings from malware binaries. Reveals hidden C2 URLs, encryption keys, commands, and configuration data that static 'strings' analysis misses. Written in Go/Rust for cross-platform speed. Essential complement to static analysis.",
        93, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "Ghidra (NSA) is a free, open-source reverse engineering framework supporting disassembly, decompilation, scripting, and collaborative analysis. Supports x86, ARM, MIPS, and many other architectures. Ghidra's decompiler converts assembly to readable C pseudocode. 2025 v11.x adds optional AI hints for function naming and crypto routine detection.",
        95, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "IDA Pro (Hex-Rays) is the gold-standard commercial disassembler and debugger for reverse engineering. Features include FLIRT signature matching, Hex-Rays decompiler, and extensive plugin ecosystem. IDA Free provides limited functionality. Widely used in vulnerability research and APT malware analysis.",
        94, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "VirusTotal aggregates 70+ antivirus engines and sandbox analysis for files, URLs, and hashes. API enables automated IoC checking. VT Intelligence provides advanced YARA-based hunting across submitted samples. VT Enterprise supports retrohunt (scanning historical submissions against new rules).",
        93, "HIGH"
    ),
    (
        "forensics-tools-malware",
        "REMnux is a free Linux distribution for reverse-engineering and analyzing malware. Pre-loaded with tools including Ghidra, Radare2, YARA, olevba (Office macro analysis), pdfid/pdf-parser (PDF malware), PEiD, and network analysis tools. Based on Ubuntu. Companion to SIFT for DFIR workflows.",
        90, "MEDIUM"
    ),

    # ========================================================================
    # 1. ESSENTIAL FORENSICS TOOLS — Endpoint / Triage
    # ========================================================================
    (
        "forensics-tools-endpoint",
        "Velociraptor is an open-source endpoint monitoring and DFIR platform (Rapid7). Uses VQL (Velociraptor Query Language) for flexible artifact collection across Windows, Linux, and macOS. Supports live response, threat hunting, and continuous monitoring at enterprise scale. WARNING: Outdated versions (0.73.4.0) have been weaponized by ransomware operators (CVE-2025-6264).",
        94, "HIGH"
    ),
    (
        "forensics-tools-endpoint",
        "KAPE (Kroll Artifact Parser and Extractor) by Eric Zimmerman is a rapid triage and collection tool for Windows forensics. Uses Targets (what to collect) and Modules (how to process). Collects Registry hives, Event Logs, Prefetch, MFT, browser artifacts, and more. Processes with EZ Tools (MFTECmd, PECmd, LECmd, etc.).",
        95, "HIGH"
    ),
    (
        "forensics-tools-endpoint",
        "Eric Zimmerman's Tools (EZ Tools) are a collection of free Windows forensic parsers: MFTECmd (MFT parser), PECmd (Prefetch), LECmd (LNK files), JLECmd (Jump Lists), RECmd/Registry Explorer (Registry), AmcacheParser, AppCompatCacheParser (ShimCache), SrumECmd (SRUM), EvtxECmd (Event Logs), and Timeline Explorer (CSV viewer).",
        96, "HIGH"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — Chain of Custody
    # ========================================================================
    (
        "forensics-chain-of-custody",
        "Chain of Custody (CoC) is the documented chronological record of evidence handling from collection through court presentation. Every person who handles evidence must be recorded with: who, what, when, where, why, and how. A broken chain can render evidence inadmissible. Must document: initial discovery, collection method, packaging, transport, storage, and every access.",
        98, "HIGH"
    ),
    (
        "forensics-chain-of-custody",
        "Digital evidence chain of custody requires: (1) Document scene with photos/video before touching anything, (2) Record device state (powered on/off, screen display), (3) Use tamper-evident bags for physical evidence, (4) Generate cryptographic hashes (SHA-256) at acquisition and verify at every transfer, (5) Maintain evidence log with timestamps and handler signatures.",
        97, "HIGH"
    ),
    (
        "forensics-chain-of-custody",
        "Blockchain-based chain of custody (2025 emerging trend): Proposed use of decentralized, immutable ledgers to log every evidence access transaction. Provides mathematical proof of custody integrity that is tamper-evident by design. Several proof-of-concept implementations exist but are not yet widely adopted in courts.",
        85, "MEDIUM"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — Evidence Preservation
    # ========================================================================
    (
        "forensics-evidence-preservation",
        "Write blockers are critical hardware or software devices that prevent any write operations to the original evidence source during examination. Hardware write blockers (Tableau/UltraBlock, WiebeTech) physically intercept write commands. Software write blockers (e.g., Windows registry-based) block at the OS level. ALWAYS use write blockers when connecting evidence drives.",
        98, "HIGH"
    ),
    (
        "forensics-evidence-preservation",
        "Forensic imaging creates an exact bit-for-bit copy (forensic image) of a storage device. Process: (1) Connect via write blocker, (2) Hash source (SHA-256), (3) Image using dd/dcfldd/FTK Imager to E01/raw format, (4) Hash the image, (5) Verify source hash == image hash for mathematical proof of integrity. Work ONLY on forensic copies, NEVER the original.",
        98, "HIGH"
    ),
    (
        "forensics-evidence-preservation",
        "Evidence storage requirements: Use ESD-safe bags for electronic devices, climate-controlled evidence rooms (avoid heat/humidity/magnetic fields), tamper-evident seals, unique evidence numbers, and a central evidence management system. Digital evidence should be stored on write-once media (WORM) or verified read-only storage with redundant backup copies.",
        92, "HIGH"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — File System Analysis
    # ========================================================================
    (
        "forensics-filesystem-analysis",
        "NTFS forensic artifacts: $MFT (Master File Table — file metadata, timestamps, sizes, parent directories), $UsnJrnl (Update Sequence Number Journal — change log of all file operations), $LogFile (transaction log for filesystem recovery), $Bitmap (allocation status), Alternate Data Streams (ADS — hidden data attached to files), $I30 index entries (directory listings including deleted files).",
        96, "HIGH"
    ),
    (
        "forensics-filesystem-analysis",
        "ext4 (Linux) forensic artifacts: Superblock (filesystem metadata), inode table (file metadata with timestamps — crtime/mtime/atime/ctime), journal (ext3/4 journaling for recovery), directory entries, deleted file recovery via inode analysis, extents for file allocation mapping. Tool: extundelete for file recovery from ext3/4.",
        93, "HIGH"
    ),
    (
        "forensics-filesystem-analysis",
        "APFS (Apple File System) forensic artifacts: Supports clones, snapshots, encryption, and space sharing. Nanosecond timestamps. APFS snapshots can preserve pre-incident state. Container/volume structure complicates traditional imaging. Tools: mac_apt, APFS Fuse, and commercial suites (Cellebrite, Magnet). APFS encryption tied to Secure Enclave on T2/M-series chips.",
        92, "HIGH"
    ),
    (
        "forensics-filesystem-analysis",
        "File carving recovers files from unallocated space based on file signatures (headers/footers), ignoring filesystem metadata. Tools: Scalpel, PhotoRec, foremost, bulk_extractor. Effective when filesystem is corrupted/overwritten. Limitation: fragmented files may not recover completely. bulk_extractor also finds emails, URLs, credit card numbers, and other artifacts.",
        91, "HIGH"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — Timeline Analysis
    # ========================================================================
    (
        "forensics-timeline-analysis",
        "Timeline analysis correlates events from multiple sources (filesystem timestamps, event logs, browser history, registry) into a unified chronological view (super timeline). Critical for establishing what happened, when, and in what order. Tool: log2timeline/plaso generates super timelines from 100+ artifact types. Output to CSV/Elasticsearch for filtering.",
        96, "HIGH"
    ),
    (
        "forensics-timeline-analysis",
        "MACB timestamps in forensic timelines: M=Modified (content changed), A=Accessed (last read), C=Changed ($MFT entry modified on NTFS; inode changed on ext4), B=Born/Created. Different filesystems track different subsets. NTFS tracks all four. FAT only tracks M and B with limited precision. Timestamp resolution varies: NTFS=100ns, FAT=2s, ext4=1s (1ns with recent kernels).",
        95, "HIGH"
    ),
    (
        "forensics-timeline-analysis",
        "Timeline analysis workflow: (1) Collect artifacts from all sources (disk, memory, logs, network), (2) Normalize timestamps to UTC, (3) Generate super timeline with plaso, (4) Filter to relevant timeframes, (5) Identify pivot points (initial compromise, lateral movement, data staging, exfiltration), (6) Corroborate findings across multiple artifact types.",
        94, "HIGH"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — Anti-Forensics Awareness
    # ========================================================================
    (
        "forensics-anti-forensics",
        "Common anti-forensics techniques: (1) Timestomping — modifying file timestamps to evade timeline analysis (detectable via $MFT vs $UsnJrnl comparison), (2) Log clearing — deleting/truncating system logs (Event ID 1102 records Security log clearing), (3) Secure wiping — overwriting data to prevent recovery, (4) Steganography — hiding data in images/audio/video files.",
        95, "HIGH"
    ),
    (
        "forensics-anti-forensics",
        "Advanced anti-forensics (2025): (1) AI-enhanced code obfuscation to bypass security tools, (2) Fileless malware executing entirely in memory (requires memory forensics), (3) Living-off-the-land binaries (LOLBins) using legitimate system tools for malicious purposes, (4) Log manipulation using anti-forensic toolkits, (5) VM-aware malware that detects sandbox environments.",
        93, "HIGH"
    ),
    (
        "forensics-anti-forensics",
        "Detecting anti-forensics: (1) Compare $MFT timestamps with $UsnJrnl entries for timestomping, (2) Check for Event ID 1102 (Security log cleared) and gaps in sequential Event IDs, (3) Analyze $MFT for files in unallocated space vs allocated space inconsistencies, (4) Use Volatility malfind plugin for injected code, (5) Cross-correlate multiple artifact sources — single artifacts can be spoofed but correlated timelines are much harder to forge.",
        94, "HIGH"
    ),
    (
        "forensics-anti-forensics",
        "Data destruction tools used in anti-forensics: BleachBit, Eraser, SDelete (Sysinternals), DBAN (Darik's Boot and Nuke), and cipher /w (Windows built-in). Detection: look for tool artifacts in Prefetch, ShimCache, Amcache, and USN Journal entries showing deletion patterns.",
        90, "MEDIUM"
    ),

    # ========================================================================
    # 2. CRITICAL FORENSICS CONCEPTS — Hash Verification
    # ========================================================================
    (
        "forensics-hash-verification",
        "Hash verification ensures evidence integrity throughout the forensic process. SHA-256 is the current standard (SHA-1 and MD5 are deprecated for integrity due to collision vulnerabilities but MD5 is still used for quick triage/deduplication). Always calculate hash BEFORE imaging, AFTER imaging, and at every evidence transfer. Matching hashes prove bit-for-bit identical copies.",
        97, "HIGH"
    ),
    (
        "forensics-hash-verification",
        "Hash databases for known file identification: NIST NSRL (National Software Reference Library) contains hash sets of known software for filtering. HashKeeper (law enforcement) and CAID/ProjectVIC (CSAM) use hash matching for rapid identification. Forensic tools use known-good and known-bad hash sets to filter results during examination.",
        92, "HIGH"
    ),
    (
        "forensics-hash-verification",
        "Fuzzy hashing (ssdeep/TLSH) identifies similar but non-identical files using context-triggered piecewise hashing. Unlike cryptographic hashes (where any change produces a completely different hash), fuzzy hashes detect modified variants of malware, documents, or images. ssdeep generates similarity scores 0-100. Useful for malware family classification.",
        90, "MEDIUM"
    ),

    # ========================================================================
    # 3. FORENSICS ARTIFACTS — Windows
    # ========================================================================
    (
        "forensics-artifacts-windows",
        "Windows Registry forensic hives: SAM (user accounts/password hashes), SECURITY (security policies/LSA secrets), SYSTEM (hardware config/services/boot info), SOFTWARE (installed programs/OS config), NTUSER.DAT (per-user settings/MRU lists/typed paths), UsrClass.dat (COM/ShellBags for folder access history). Location: C:\\Windows\\System32\\config\\ and user profile directories.",
        97, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows Event Logs (EVTX) critical Event IDs: 4624/4625 (logon success/failure), 4648 (explicit credential logon), 4688 (process creation — enable command line auditing), 4697/7045 (service installation — persistence indicator), 1102 (Security log cleared — anti-forensics), 4720 (user account created), 4732 (user added to group). Logs in C:\\Windows\\System32\\winevt\\Logs\\.",
        97, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows Prefetch files (.pf) in C:\\Windows\\Prefetch\\ record evidence of program execution: executable name, run count, last 8 run timestamps (Win10+), and files/directories referenced during first 10 seconds of execution. Limited to 1024 entries (Win10/11). Requires EnablePrefetcher registry value >= 1. Parse with PECmd (Eric Zimmerman).",
        96, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows $MFT (Master File Table) contains metadata for every file on NTFS: filename, full path, MACB timestamps ($STANDARD_INFORMATION and $FILE_NAME attributes), file size, flags, and parent directory reference. $FILE_NAME timestamps are harder to spoof than $STANDARD_INFORMATION — compare both for timestomping detection. Parse with MFTECmd.",
        96, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows $UsnJrnl (Update Sequence Number Journal) records file system changes: file creation, deletion, rename, content modification, and attribute changes. Located at $Extend\\$UsnJrnl:$J (an ADS). Provides forensic evidence of file operations even after files are deleted. Entries include timestamps, filename, parent MFT reference, and reason flags. Parse with MFTECmd.",
        95, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Amcache.hve (C:\\Windows\\appcompat\\Programs\\Amcache.hve) is a Registry hive tracking application execution, installed programs, drivers, and shortcuts. Records SHA-1 hashes of executables, file paths, file sizes, and timestamps. Provides live execution data (unlike ShimCache which captures at shutdown). More reliable indicator of execution than ShimCache. Parse with AmcacheParser.",
        95, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "ShimCache (Application Compatibility Cache) in SYSTEM registry hive records executables observed by the OS. Tracks file path, file size, and last modified timestamp. Written at shutdown/reboot (not real-time). Does NOT definitively prove execution — only that the OS was aware of the file. Updated in insert order. Parse with AppCompatCacheParser.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "SRUM (System Resource Usage Monitor) database at C:\\Windows\\System32\\sru\\SRUDB.dat tracks per-application resource usage on Windows 8+: network bytes sent/received per app, CPU time, energy usage, and more. Data retained for 30-60 days. Can prove application usage and network activity even after logs are cleared. Parse with SrumECmd.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows Jump Lists and LNK files: Jump Lists (Recent, Frequent, Pinned in user profile\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\AutomaticDestinations) record files accessed per application with timestamps. LNK shortcut files record target path, MAC timestamps of target, volume serial number, and machine ID. Parse with JLECmd and LECmd.",
        93, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows browser artifacts: Chrome/Edge/Brave store History, Cookies, Login Data, and Cache in SQLite databases under AppData\\Local. Firefox uses places.sqlite (history/bookmarks) and cookies.sqlite. Browser data reveals URL history, downloads, search queries, cached pages, saved passwords, and autofill data. Tools: Hindsight (Chrome), KAPE browser modules.",
        92, "HIGH"
    ),
    (
        "forensics-artifacts-windows",
        "Windows RDP forensic artifacts: Event IDs 21/22/24/25 in Microsoft-Windows-TerminalServices-LocalSessionManager (logon/shell/disconnect/reconnect), Event ID 1149 in TerminalServices-RemoteConnectionManager (initial connection), Bitmap Cache in AppData\\Local\\Microsoft\\Terminal Server Client\\Cache (reconstructable screen tiles), Default.rdp for saved connections.",
        93, "HIGH"
    ),

    # ========================================================================
    # 3. FORENSICS ARTIFACTS — Linux
    # ========================================================================
    (
        "forensics-artifacts-linux",
        "Linux /var/log key files: auth.log/secure (authentication events, sudo usage, SSH logins), syslog/messages (general system events), kern.log (kernel messages, driver loading, USB connections), dpkg.log/yum.log (package installation history), faillog (failed login attempts), lastlog (last login per user). Note: systemd journal is replacing traditional log files.",
        95, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux bash_history (~/.bash_history per user, /root/.bash_history for root) records executed commands. Written to disk only when shell exits — live shell history is in memory only. Old .bash_history files persist as deleted inodes recoverable through file carving. Check HISTFILE, HISTSIZE, HISTCONTROL env vars for manipulation. Also check .zsh_history, .python_history.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux wtmp/btmp/utmp (binary files): wtmp (/var/log/wtmp) records login/logout history (parse with 'last' command), btmp (/var/log/btmp) records failed login attempts (parse with 'lastb'), utmp (/var/run/utmp) records currently logged-in users (parse with 'who'/'w'). These are binary — must use utilities, not text editors.",
        93, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux systemd journal (/var/log/journal/ or /run/log/journal/) is the modern logging system replacing syslog. View with journalctl: --file <path> (specific journal), -u <unit> (by service), --since/--until (time range), -p <priority> (by severity), -k (kernel messages). Journal captures USB connections, network interfaces, service state, logins, and application errors.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux cron forensics: User crontabs in /var/spool/cron/crontabs/<username>, system cron in /etc/crontab and /etc/cron.d/*, and cron execution logs in syslog/journal. Attackers use cron for persistence — check for unusual entries, encoded commands, reverse shells, and recently modified crontab files. Also check systemd timers: systemctl list-timers.",
        92, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux /proc filesystem provides live system state: /proc/<pid>/cmdline (full command line), /proc/<pid>/exe (symlink to binary), /proc/<pid>/fd/ (open file descriptors), /proc/<pid>/maps (memory mappings), /proc/<pid>/environ (environment variables), /proc/net/tcp (active connections). Volatile — capture during live response before reboot.",
        93, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux /tmp analysis: /tmp is world-writable and commonly used by attackers for staging tools, scripts, and exfiltrated data. Check for: unusual executables, encoded scripts, SSH keys, compiled exploits, recently created files. Also check /dev/shm (tmpfs in RAM — disappears on reboot), /var/tmp (survives reboots), and hidden directories (.xxx, ..., etc.).",
        91, "HIGH"
    ),
    (
        "forensics-artifacts-linux",
        "Linux persistence mechanisms to check: /etc/rc.local, /etc/init.d/ scripts, systemd service files (/etc/systemd/system/, ~/.config/systemd/user/), cron jobs, .bashrc/.profile modifications, authorized_keys (SSH), LD_PRELOAD (/etc/ld.so.preload), kernel modules (/lib/modules/), and at jobs (/var/spool/at/).",
        93, "HIGH"
    ),

    # ========================================================================
    # 3. FORENSICS ARTIFACTS — macOS
    # ========================================================================
    (
        "forensics-artifacts-macos",
        "macOS FSEvents (File System Events) stored in /.fseventsd/ record all filesystem activity: file creation, modification, deletion, and renaming across entire directory structures. Records persist even for deleted files and unmounted volumes. Each record includes event path, event ID, and flags. Critical for reconstructing user file operations and detecting data destruction.",
        95, "HIGH"
    ),
    (
        "forensics-artifacts-macos",
        "macOS Spotlight metadata database (/.Spotlight-V100/) indexes file content and metadata for search. Contains file attributes, content previews, and metadata even after files are deleted. Can reveal evidence of files that no longer exist on the filesystem. Tool: mdls (metadata listing), mdfind (search). Store.db uses proprietary format — use mac_apt or commercial tools.",
        93, "HIGH"
    ),
    (
        "forensics-artifacts-macos",
        "macOS KnowledgeC database (~/Library/Application Support/Knowledge/knowledgeC.db) tracks detailed user activity: app usage duration, screen time, device lock/unlock events, media playback, Safari browsing, Siri usage, and focus/attention state. Retains data for weeks to months. SQLite format, parseable with standard SQL tools. Powerful for establishing user activity timelines.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-macos",
        "macOS Unified Logs (log show/log collect commands) consolidate logs from all system components into a single structured logging system. Include application logs, system events, kernel messages, and more. Rich forensic data: device connections, user authorizations, Bluetooth activity, network changes, and notifications. Use: log show --predicate 'eventMessage contains \"keyword\"' --info --debug.",
        95, "HIGH"
    ),
    (
        "forensics-artifacts-macos",
        "macOS Quarantine Events database (~/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2) logs all files downloaded from external sources (Internet, AirDrop, email). Records: source URL, download timestamp, application used to download, and the quarantine flag. Data persists even after downloaded files are deleted. Essential for tracking malware delivery.",
        94, "HIGH"
    ),
    (
        "forensics-artifacts-macos",
        "macOS additional artifacts: .DS_Store files (folder view preferences, can reveal deleted filenames), TCC.db (privacy permission grants — camera, microphone, screen recording, full disk access), LaunchAgents/LaunchDaemons (persistence — check ~/Library/LaunchAgents and /Library/LaunchDaemons), and Apple System Log (ASL) for pre-Unified Log systems.",
        92, "HIGH"
    ),

    # ========================================================================
    # 4. FORENSICS METHODOLOGIES — NIST SP 800-86
    # ========================================================================
    (
        "forensics-methodology-nist",
        "NIST SP 800-86 (Guide to Integrating Forensic Techniques into Incident Response) defines four phases of digital forensics: (1) Collection — identify, label, record, and acquire data while preserving integrity, (2) Examination — process collected data using manual/automated methods, (3) Analysis — analyze examination results to derive useful information, (4) Reporting — document findings and present results.",
        97, "HIGH"
    ),
    (
        "forensics-methodology-nist",
        "NIST SP 800-86 data source categories: (1) Files — documents, images, executables, (2) Operating System — logs, configuration, artifacts, (3) Network Traffic — packets, flows, connection logs, (4) Application — databases, logs, cached data. Each source has unique collection and examination considerations. Framework emphasizes consistent, repeatable, documented processes.",
        94, "HIGH"
    ),
    (
        "forensics-methodology-nist",
        "NIST SP 800-86 vs ISO/IEC 27037: NIST provides practical guidance from an IT perspective (not law enforcement). ISO 27037 provides guidelines for identification, collection, acquisition, and preservation of digital evidence. ISO standard is internationally recognized for cross-border investigations. Best practice: align with both standards for comprehensive coverage.",
        90, "MEDIUM"
    ),

    # ========================================================================
    # 4. FORENSICS METHODOLOGIES — RFC 3227
    # ========================================================================
    (
        "forensics-methodology-rfc3227",
        "RFC 3227 (Guidelines for Evidence Collection and Archiving) establishes the order of volatility for evidence collection — collect most volatile first: (1) CPU registers/cache, (2) Routing table/ARP cache/process table/kernel stats, (3) Memory (RAM), (4) Temporary file systems (/tmp, swap), (5) Disk, (6) Remote logging/monitoring data, (7) Physical configuration/network topology, (8) Archival media (backups/tapes).",
        97, "HIGH"
    ),
    (
        "forensics-methodology-rfc3227",
        "RFC 3227 key principles: (1) Capture an accurate picture of the system, (2) Keep detailed notes (what, when, who), (3) Minimize changes to the evidence, (4) Remove external avenues for change (isolate from network), (5) When in doubt, collect more rather than less, (6) Document every action taken, (7) Ensure actions are repeatable by an independent party.",
        96, "HIGH"
    ),

    # ========================================================================
    # 4. FORENSICS METHODOLOGIES — SANS DFIR
    # ========================================================================
    (
        "forensics-methodology-sans",
        "SANS Incident Response Framework (PICERL) — six phases: (1) Preparation — policies, CSIRT, tools, training, (2) Identification — detect and validate security events, (3) Containment — short-term (isolate) and long-term (remediate) containment, (4) Eradication — remove threat, patch vulnerabilities, (5) Recovery — restore systems, verify clean state, monitor, (6) Lessons Learned — retrospective within 2 weeks, document improvements.",
        97, "HIGH"
    ),
    (
        "forensics-methodology-sans",
        "SANS DFIR key training tracks (2025): FOR500 (Windows Forensic Analysis), FOR508 (Advanced Incident Response/Threat Hunting), FOR572 (Advanced Network Forensics), FOR610 (Reverse-Engineering Malware), FOR498 (Battlefield Forensics — triage and acquisition). GIAC certifications: GCFE, GCFA, GNFA, GREM. Industry gold standard for DFIR professional development.",
        93, "HIGH"
    ),
    (
        "forensics-methodology-sans",
        "SANS Incident Response vs NIST comparison: SANS PICERL is more technically prescriptive with six distinct phases. NIST SP 800-61 uses four phases (Preparation, Detection/Analysis, Containment/Eradication/Recovery, Post-Incident Activity). Both are widely accepted. SANS provides deeper tactical guidance; NIST provides broader organizational framework.",
        91, "MEDIUM"
    ),

    # ========================================================================
    # 4. FORENSICS METHODOLOGIES — Incident Response Frameworks
    # ========================================================================
    (
        "forensics-methodology-ir",
        "MITRE ATT&CK framework maps adversary tactics, techniques, and procedures (TTPs) used in real-world attacks. 14 tactics from Initial Access through Impact. Use for: threat-informed defense, detection engineering, incident analysis, and red team operations. ATT&CK Navigator visualizes coverage gaps. Essential for mapping forensic findings to attacker behavior.",
        96, "HIGH"
    ),
    (
        "forensics-methodology-ir",
        "Cyber Kill Chain (Lockheed Martin) models attack progression: (1) Reconnaissance, (2) Weaponization, (3) Delivery, (4) Exploitation, (5) Installation, (6) Command & Control, (7) Actions on Objectives. Forensic analysis maps evidence to each phase. Defense aims to break the chain at the earliest possible stage. Complement with MITRE ATT&CK for granular TTP mapping.",
        93, "HIGH"
    ),
    (
        "forensics-methodology-ir",
        "Diamond Model of Intrusion Analysis relates four core features of every intrusion event: Adversary, Infrastructure, Capability, and Victim. Each event can be analyzed and correlated across these dimensions. Useful for clustering related incidents, attributing campaigns, and building adversary profiles from forensic evidence.",
        89, "MEDIUM"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — Imaging (Linux CLI)
    # ========================================================================
    (
        "forensics-commands-imaging",
        "dd forensic imaging: sudo dd if=/dev/sdX of=/path/to/image.raw bs=4M status=progress conv=sync,noerror — 'conv=noerror' continues past read errors, 'conv=sync' pads error sectors with zeros, 'bs=4M' for efficient throughput, 'status=progress' shows transfer rate. Always hash before and after: sha256sum /dev/sdX && sha256sum image.raw",
        96, "HIGH"
    ),
    (
        "forensics-commands-imaging",
        "dcfldd forensic imaging: sudo dcfldd if=/dev/sdX of=/path/image.raw hash=sha256 hashlog=hash.txt hashwindow=1G bs=4M — provides on-the-fly hashing, progress reporting, and hash verification. Verify: dcfldd if=/dev/sdX vf=/path/image.raw verifylog=verify.txt. Supports simultaneous output to multiple destinations for duplicate images.",
        95, "HIGH"
    ),
    (
        "forensics-commands-imaging",
        "ewfacquire (from libewf) creates EnCase E01 format images with compression, metadata, and built-in hash verification: ewfacquire /dev/sdX -t /path/output -C 'Case-001' -D 'Suspect HD' -e 'Examiner Name' -f encase6 -c deflate:best -S 2GB. E01 format is court-accepted and includes case metadata, hash verification, and compression.",
        93, "HIGH"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — File Analysis (Linux CLI)
    # ========================================================================
    (
        "forensics-commands-fileanalysis",
        "File identification commands: 'file <path>' identifies file type by magic bytes (not extension), 'strings -a -n 8 <file>' extracts printable strings (minimum 8 chars, all sections), 'strings -e l <file>' for UTF-16LE strings (Windows), 'xxd <file> | head -50' hex dump first 800 bytes, 'hexdump -C <file> | head' canonical hex+ASCII view.",
        95, "HIGH"
    ),
    (
        "forensics-commands-fileanalysis",
        "Hash calculation commands: sha256sum <file> (SHA-256), md5sum <file> (MD5 — triage only), sha1sum <file> (SHA-1 — legacy), sha256deep -r /path/ (recursive directory hashing). Compare: diff <(sha256sum file1) <(sha256sum file2). Batch: find /evidence -type f -exec sha256sum {} \\; > manifest.sha256",
        94, "HIGH"
    ),
    (
        "forensics-commands-fileanalysis",
        "Metadata extraction: exiftool <file> (EXIF/metadata for images, documents, PDFs — reveals camera model, GPS coordinates, software, author, timestamps), pdfinfo <file> (PDF metadata), olevba <file> (extract VBA macros from Office docs — malware analysis), pdfid <file> (identify suspicious PDF keywords like /JavaScript, /OpenAction, /Launch).",
        92, "HIGH"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — Volatility 3 Plugins
    # ========================================================================
    (
        "forensics-commands-volatility",
        "Volatility 3 process analysis: vol -f memdump.raw windows.pslist (process listing), windows.pstree (process tree), windows.psscan (scan for hidden/terminated processes), windows.cmdline (command-line arguments), windows.dlllist (loaded DLLs per process), windows.handles (open handles). Compare pslist vs psscan to detect process hiding (DKOM attacks).",
        96, "HIGH"
    ),
    (
        "forensics-commands-volatility",
        "Volatility 3 network analysis: vol -f memdump.raw windows.netscan (active and closed network connections with timestamps), windows.netstat (active connections only). Key fields: local/remote IP:port, state, PID, owner process. Cross-reference PIDs with pslist to identify processes making suspicious network connections.",
        95, "HIGH"
    ),
    (
        "forensics-commands-volatility",
        "Volatility 3 malware detection: vol -f memdump.raw windows.malfind (detect injected code — RWX memory regions not backed by files), windows.vadinfo (Virtual Address Descriptor analysis), windows.ssdt (System Service Descriptor Table hooks), windows.modules (loaded kernel modules), windows.modscan (scan for hidden modules). malfind is the primary plugin for detecting code injection.",
        95, "HIGH"
    ),
    (
        "forensics-commands-volatility",
        "Volatility 3 credential extraction: vol -f memdump.raw windows.hashdump (extract password hashes from SAM), windows.lsadump (LSA secrets), windows.cachedump (cached domain credentials). Registry analysis: windows.registry.hivelist (list loaded hives), windows.registry.printkey (read registry keys), windows.registry.userassist (program execution evidence).",
        94, "HIGH"
    ),
    (
        "forensics-commands-volatility",
        "Volatility 3 Linux plugins: vol -f memdump.lime linux.pslist (process listing), linux.pstree, linux.bash (bash history from memory — recovers commands not yet flushed to .bash_history), linux.lsmod (loaded kernel modules), linux.check_syscall (detect syscall table hooks/rootkits), linux.sockstat (socket connections), linux.mount (mounted filesystems).",
        94, "HIGH"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — Plaso/log2timeline
    # ========================================================================
    (
        "forensics-commands-plaso",
        "Plaso (log2timeline) super timeline creation: log2timeline.py --storage-file output.plaso /path/to/evidence/image.E01 — processes disk image and extracts timestamps from 100+ artifact types (filesystem, registry, event logs, browser, etc.). For mounted evidence: log2timeline.py --storage-file output.plaso /mnt/evidence/",
        96, "HIGH"
    ),
    (
        "forensics-commands-plaso",
        "Plaso output and filtering: psort.py --output-time-zone 'UTC' -o l2tcsv -w timeline.csv output.plaso \"date > datetime('2025-01-01T00:00:00') AND date < datetime('2025-03-01T00:00:00')\" — filters by date range and exports to CSV. Other outputs: -o json_line (JSON lines), -o elastic (direct to Elasticsearch). Use pinfo.py output.plaso for storage file details.",
        95, "HIGH"
    ),
    (
        "forensics-commands-plaso",
        "Plaso quick triage with psteal: psteal.py --source /path/to/image.E01 -o l2tcsv -w timeline.csv — combines log2timeline and psort into a single command for rapid timeline generation. Useful for incident response when speed is critical. Full pipeline for large cases: log2timeline -> psort with filters -> Timeline Explorer or Elasticsearch/Kibana for analysis.",
        93, "HIGH"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — YARA Scanning
    # ========================================================================
    (
        "forensics-commands-yara",
        "YARA scanning commands: yara rules.yar /path/to/file (single file), yara -r rules.yar /path/to/dir (recursive directory scan), yara -s rules.yar file (print matching strings), yara -m rules.yar file (print rule metadata), yara -p 8 -r rules.yar /dir (8 threads parallel scan), yara -C compiled.bin -r /dir (use precompiled rules for speed).",
        95, "HIGH"
    ),
    (
        "forensics-commands-yara",
        "YARA rule structure: rule RuleName { meta: author='analyst' description='Detects X' / strings: $s1='malicious_string' $h1={48 65 6C 6C 6F} $r1=/https?:\\/\\/[a-z]+\\.evil\\.com/ / condition: any of ($s*) or $h1 }. Three sections: meta (optional metadata), strings (text, hex, regex patterns), condition (boolean logic combining string matches).",
        94, "HIGH"
    ),
    (
        "forensics-commands-yara",
        "YARA with other tools: Use YARA rules in Volatility 3 (yarascan plugin for memory scanning), Cuckoo/CAPE sandbox (automatic rule matching on samples), ClamAV (YARA rule integration), and SIEM platforms. Community rule sets: YARA-Rules (GitHub), Malpedia YARA rules, Florian Roth's signature-base, and Abuse.ch YARA feeds.",
        92, "HIGH"
    ),

    # ========================================================================
    # 5. COMMON FORENSIC COMMANDS — Additional CLI Tools
    # ========================================================================
    (
        "forensics-commands-cli",
        "Evidence mounting: mount -o ro,noexec,nosuid,loop image.raw /mnt/evidence (read-only mount of raw image), ewfmount image.E01 /mnt/ewf && mount -o ro,noexec /mnt/ewf/ewf1 /mnt/evidence (E01 mount via FUSE). Always mount read-only (-o ro). Use losetup for partition offset: losetup -o $((512*2048)) /dev/loop0 image.raw",
        94, "HIGH"
    ),
    (
        "forensics-commands-cli",
        "Filesystem timeline with TSK: fls -r -m '/' /path/to/image.raw > bodyfile.txt && mactime -b bodyfile.txt -d > timeline.csv — fls extracts file listing recursively, mactime converts to CSV timeline with MACB timestamps. Add -z UTC for timezone normalization. Quick alternative to full plaso for targeted filesystem analysis.",
        93, "HIGH"
    ),
    (
        "forensics-commands-cli",
        "bulk_extractor scans disk images or files for artifacts without filesystem parsing: bulk_extractor -o output_dir image.raw — extracts emails, URLs, credit card numbers, phone numbers, GPS coordinates, JPEG/PNG images, Windows PE files, JSON, and more. Results in feature files. Supports multithreaded operation for fast processing of large images.",
        92, "HIGH"
    ),
    (
        "forensics-commands-cli",
        "Network forensic CLI: tshark -r capture.pcap -Y 'http.request' -T fields -e http.host -e http.request.uri (extract HTTP requests), tcpdump -r capture.pcap -n 'port 53' (DNS traffic), ngrep -I capture.pcap 'password' (search packet payloads), editcap -c 10000 large.pcap split.pcap (split large PCAPs).",
        91, "HIGH"
    ),
]


def seed_brain(dry_run: bool = False) -> dict:
    """Seed the Diamond Brain with all forensics knowledge.

    Args:
        dry_run: If True, print entries without writing to brain.

    Returns:
        Summary dict with counts per category and total.
    """
    brain = DiamondBrain()
    category_counts = {}
    total = 0
    skipped = 0

    for category, fact, confidence, severity in FORENSICS_KNOWLEDGE:
        # Prefix fact with severity tag for easy filtering
        tagged_fact = f"[{severity}] {fact}"

        if dry_run:
            print(f"  [{confidence:>3}%] {category}: {fact[:80]}...")
        else:
            brain.learn(
                topic=category,
                fact=tagged_fact,
                confidence=confidence,
                source="forensics-research-2025",
                verified=True,  # Research-verified facts
            )

        category_counts[category] = category_counts.get(category, 0) + 1
        total += 1

    return {
        "total_facts_seeded": total,
        "categories": category_counts,
        "unique_categories": len(category_counts),
        "dry_run": dry_run,
    }


def print_summary(result: dict) -> None:
    """Print a formatted summary of the seeding operation."""
    print()
    print("=" * 70)
    print("  DIGITAL FORENSICS KNOWLEDGE SEED — COMPLETE")
    print("=" * 70)
    print()
    print(f"  Total facts seeded : {result['total_facts_seeded']}")
    print(f"  Unique categories  : {result['unique_categories']}")
    print(f"  Mode               : {'DRY RUN (no writes)' if result['dry_run'] else 'LIVE (written to brain)'}")
    print()
    print("  Facts per category:")
    print("  " + "-" * 50)
    for cat, count in sorted(result["categories"].items()):
        print(f"    {cat:<40} {count:>3}")
    print()


def print_post_seed_stats() -> None:
    """Print brain statistics after seeding."""
    brain = DiamondBrain()
    digest = brain.digest()
    heatmap = brain.heatmap()

    print()
    print("=" * 70)
    print("  DIAMOND BRAIN — POST-SEED STATISTICS")
    print("=" * 70)
    print()
    print(f"  Total facts in brain : {digest['total_facts']}")
    print(f"  Total topics         : {len(digest['topics'])}")
    print(f"  Last updated         : {digest['last_updated']}")
    print()
    print("  Topic heatmap:")
    print("  " + "-" * 60)
    for topic, info in sorted(heatmap.items(),
                               key=lambda x: x[1]["count"], reverse=True):
        bar = "|" * min(info["count"] * 2, 30)
        print(f"    {topic:<40} {info['count']:>3} facts  [{bar}]")
    print()

    # Test a few recalls to verify
    print("  Sample recalls:")
    print("  " + "-" * 60)
    test_queries = [
        "forensics-tools-disk",
        "forensics-artifacts-windows",
        "forensics-commands-volatility",
        "forensics-methodology-nist",
    ]
    for q in test_queries:
        results = brain.recall(q, max_results=2, min_confidence=85)
        if results:
            for r in results:
                fact_preview = r["fact"][:75] + "..." if len(r["fact"]) > 75 else r["fact"]
                print(f"    [{r['confidence']:>3}%] {q}: {fact_preview}")
        else:
            print(f"    (no results for '{q}')")
    print()


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        result = seed_brain(dry_run=True)
        print_summary(result)
    elif "--stats" in sys.argv:
        print_post_seed_stats()
    else:
        result = seed_brain(dry_run=False)
        print_summary(result)
        print_post_seed_stats()
