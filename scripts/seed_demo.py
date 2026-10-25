"""
演示数据种子脚本。
插入真实感的 ISCA 2027 论文、审稿人、匹配分数和分配数据。
运行：cd ~/Desktop/paper-reviewer-match && source .venv/bin/activate && python scripts/seed_demo.py
"""
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "reviewmatch.db"

# ── 论文数据（基于真实 ISCA/ASPLOS 研究方向）─────────────────────────────
PAPERS = [
    {
        "title": "MemFlow: Rethinking Cache Hierarchy for Disaggregated Memory Systems",
        "abstract": "We propose MemFlow, a novel cache hierarchy design for disaggregated memory systems. By decoupling capacity from bandwidth, MemFlow reduces memory access latency by 3.2× while maintaining full coherence guarantees across 64-node clusters.",
        "authors": [
            {"name": "Jiaming Chen", "institution": "MIT CSAIL"},
            {"name": "Sarah K. Hoffman", "institution": "MIT CSAIL"},
            {"name": "David Park", "institution": "Google Brain"},
        ],
        "topics": ["Disaggregated Memory", "Cache Hierarchy", "Cache Coherence", "Memory Access Latency"],
        "methods": ["Cycle-accurate simulation", "Hardware prototype", "Workload benchmarking"],
        "required_expertise": ["Computer Architecture", "Memory Systems", "Cache Coherence Protocols"],
        "status": "analyzed",
    },
    {
        "title": "SparsePIM: Efficient Sparse Tensor Operations on Processing-In-Memory Architectures",
        "abstract": "SparsePIM introduces a hardware-software co-design for accelerating sparse tensor operations on PIM architectures. Our approach achieves 8.7× speedup over state-of-the-art GPU solutions for sparse GNN inference workloads.",
        "authors": [
            {"name": "Yuxin Wang", "institution": "Tsinghua University"},
            {"name": "Lin Zhao", "institution": "Tsinghua University"},
            {"name": "Robert Hanson", "institution": "Samsung Research"},
        ],
        "topics": ["Processing-In-Memory", "Sparse Computing", "Graph Neural Networks", "Hardware Accelerator"],
        "methods": ["RTL simulation", "FPGA prototype", "Roofline analysis"],
        "required_expertise": ["PIM Architecture", "Sparse Computation", "Machine Learning Accelerators"],
        "status": "analyzed",
    },
    {
        "title": "TLBshot: Mitigating TLB Shootdown Bottlenecks in Many-Core Processors",
        "abstract": "TLB shootdown is a critical scalability bottleneck in modern many-core systems. TLBshot introduces a hardware-assisted selective invalidation mechanism that reduces shootdown overhead by 91% in virtualized cloud workloads.",
        "authors": [
            {"name": "Elena Vasquez", "institution": "ETH Zurich"},
            {"name": "Marco Bianchi", "institution": "ETH Zurich"},
        ],
        "topics": ["TLB Management", "Virtual Memory", "Many-Core Architecture", "Virtualization"],
        "methods": ["Full-system simulation", "Linux kernel modification", "Cloud workload analysis"],
        "required_expertise": ["Operating Systems", "Virtual Memory Management", "Many-Core Systems"],
        "status": "analyzed",
    },
    {
        "title": "Photonic-Electronic Hybrid Interconnects for Data Center Scale AI Training",
        "abstract": "We present a photonic-electronic hybrid interconnect fabric that achieves 400 Gbps/mm² bandwidth density at 1.2 pJ/bit energy efficiency. Deployed on a 1024-GPU cluster, it reduces AllReduce communication time by 5.1× compared to traditional electrical interconnects.",
        "authors": [
            {"name": "Aisha Patel", "institution": "Stanford University"},
            {"name": "Thomas Nguyen", "institution": "Stanford University"},
            {"name": "Jennifer Wu", "institution": "Intel Labs"},
            {"name": "Carlos Rivera", "institution": "Intel Labs"},
        ],
        "topics": ["Photonic Interconnects", "Data Center Networking", "AI Training Infrastructure", "Optical Computing"],
        "methods": ["Silicon photonics tape-out", "Network simulation", "End-to-end system evaluation"],
        "required_expertise": ["Computer Networks", "Photonic Systems", "Distributed Machine Learning"],
        "status": "analyzed",
    },
    {
        "title": "RISC-V Vector Extension for Genomic Sequence Alignment Acceleration",
        "abstract": "We extend the RISC-V vector ISA with genomics-specific instructions for Smith-Waterman and SIMD-accelerated BWA-MEM. Our FPGA implementation achieves 120× speedup over software baselines while maintaining exact alignment results.",
        "authors": [
            {"name": "Kenji Tanaka", "institution": "University of Tokyo"},
            {"name": "Priya Krishnamurthy", "institution": "UC Berkeley"},
        ],
        "topics": ["RISC-V", "Bioinformatics Acceleration", "ISA Extension", "Genomics Computing"],
        "methods": ["ISA design", "FPGA implementation", "Genomics benchmark suite"],
        "required_expertise": ["Processor Architecture", "Domain-Specific Acceleration", "Bioinformatics"],
        "status": "analyzed",
    },
    {
        "title": "Chronos: Temporal Speculation for Out-of-Order Memory Consistency in Shared-Memory Systems",
        "abstract": "Chronos introduces temporal speculation to allow processors to execute memory operations out of order while maintaining sequential consistency. We demonstrate 23% IPC improvement on SPEC CPU2017 with hardware overhead under 3%.",
        "authors": [
            {"name": "Michael Zhang", "institution": "Carnegie Mellon University"},
            {"name": "Stephanie O'Brien", "institution": "Carnegie Mellon University"},
            {"name": "Felix Müller", "institution": "TU Munich"},
        ],
        "topics": ["Memory Consistency", "Speculative Execution", "Out-of-Order Processors", "Hardware Speculation"],
        "methods": ["Microarchitectural simulation", "Formal verification", "SPEC benchmark evaluation"],
        "required_expertise": ["Memory Consistency Models", "Microarchitecture", "Formal Methods"],
        "status": "analyzed",
    },
    {
        "title": "NeuralPrefetch: Learning Memory Access Patterns with On-Chip Transformers",
        "abstract": "We propose embedding a lightweight transformer model directly into the L2 prefetcher, trained online using compressed access stream representations. NeuralPrefetch achieves 94% accuracy on irregular access patterns, outperforming LSTM-based approaches by 31%.",
        "authors": [
            {"name": "Sophie Martin", "institution": "INRIA Paris"},
            {"name": "Hugo Leclerc", "institution": "INRIA Paris"},
        ],
        "topics": ["Hardware Prefetching", "Machine Learning for Architecture", "Memory Access Prediction", "On-chip ML"],
        "methods": ["Gem5 simulation", "Online learning evaluation", "Silicon area analysis"],
        "required_expertise": ["Prefetching Algorithms", "Machine Learning", "Memory Hierarchy Design"],
        "status": "analyzed",
    },
    {
        "title": "SafeStack: Hardware-Enforced Control Flow Integrity for RISC-V Embedded Systems",
        "abstract": "SafeStack adds a hardware-enforced shadow stack and CFI mechanism to RISC-V, protecting against ROP and JOP attacks with less than 2% runtime overhead. We validate against 47 known CVEs without false positives.",
        "authors": [
            {"name": "Lars Eriksson", "institution": "KTH Royal Institute"},
            {"name": "Anna Johansson", "institution": "KTH Royal Institute"},
            {"name": "David Osei", "institution": "ARM Research"},
        ],
        "topics": ["Hardware Security", "Control Flow Integrity", "RISC-V Security", "Embedded Systems"],
        "methods": ["RTL implementation", "Security validation suite", "Performance analysis"],
        "required_expertise": ["Computer Security", "Processor Design", "Embedded Systems Architecture"],
        "status": "analyzed",
    },
    {
        "title": "CXL-Fabric: Composable Memory Pooling with CXL 3.0 for HPC Workloads",
        "abstract": "We design CXL-Fabric, a runtime system for dynamically composing memory pools across CXL 3.0 switches. Evaluated on 16 HPC benchmarks, CXL-Fabric reduces memory provisioning waste by 67% while meeting 99th-percentile latency SLOs.",
        "authors": [
            {"name": "Raj Patel", "institution": "University of Michigan"},
            {"name": "Nicole Brown", "institution": "University of Michigan"},
            {"name": "Sung-Jin Lee", "institution": "SK Hynix"},
        ],
        "topics": ["CXL", "Memory Pooling", "High Performance Computing", "Memory Fabric"],
        "methods": ["CXL 3.0 emulation", "HPC workload evaluation", "Queueing theory modeling"],
        "required_expertise": ["CXL Protocol", "Memory Systems", "High Performance Computing"],
        "status": "analyzed",
    },
    {
        "title": "Thermal-Aware Floorplanning for 3D-Stacked Chiplet Architectures",
        "abstract": "We present a thermal-aware floorplanning framework for 3D-stacked chiplet designs that co-optimizes performance and thermal dissipation. Our ILP-based approach reduces peak temperature by 18°C while achieving within 4% of optimal performance.",
        "authors": [
            {"name": "Wei-Ting Huang", "institution": "National Taiwan University"},
            {"name": "Chieh-Lin Chu", "institution": "National Taiwan University"},
        ],
        "topics": ["3D Integration", "Chiplet Architecture", "Thermal Management", "Floorplanning"],
        "methods": ["ILP optimization", "Thermal simulation", "Commercial EDA tool integration"],
        "required_expertise": ["VLSI Design", "3D Chip Integration", "Thermal Engineering"],
        "status": "analyzed",
    },
    {
        "title": "Quantum Error Mitigation via Classical Post-Processing on NISQ Devices",
        "abstract": "We propose a classical post-processing pipeline that mitigates quantum noise on NISQ devices without additional qubit overhead. Applied to variational quantum algorithms, our method reduces error rates by 73% at the cost of 2.1× classical compute.",
        "authors": [
            {"name": "Isabella Romano", "institution": "Politecnico di Milano"},
            {"name": "James Liu", "institution": "IBM Quantum"},
        ],
        "topics": ["Quantum Computing", "Error Mitigation", "NISQ Architecture", "Quantum-Classical Co-design"],
        "methods": ["Quantum circuit simulation", "Error characterization", "Statistical modeling"],
        "required_expertise": ["Quantum Computing", "Computer Architecture", "Noise Analysis"],
        "status": "analyzing",
    },
    {
        "title": "Accelerating Transformer Inference with Structured Sparsity on Custom ASICs",
        "abstract": "We co-design a structured sparsity pattern and a custom ASIC that achieves 12× inference speedup for large language models with less than 1% accuracy degradation on standard NLP benchmarks.",
        "authors": [
            {"name": "Hana Kim", "institution": "KAIST"},
            {"name": "Minjoon Oh", "institution": "KAIST"},
            {"name": "Grace Chen", "institution": "Apple Silicon"},
        ],
        "topics": ["Transformer Acceleration", "Structured Sparsity", "ASIC Design", "LLM Inference"],
        "methods": ["ASIC tape-out", "Sparsity training", "MLPerf benchmark"],
        "required_expertise": ["Deep Learning Accelerators", "ASIC Design", "NLP Model Compression"],
        "status": "pending",
    },
]

# ── 审稿人数据（真实感，基于 ISCA PC 典型背景）───────────────────────────
REVIEWERS = [
    {
        "name": "Margaret Martonosi",
        "email": "martonosi@princeton.edu",
        "institution": "Princeton University",
        "scholar_url": "https://scholar.google.com/citations?user=martonosi",
        "fetch_status": "done",
        "expertise_topics": ["Computer Architecture", "Memory Systems", "Mobile Computing", "Power-Efficient Design"],
        "publications": [
            {"title": "MemSpy: Analyzing Memory System Bottlenecks in Programs", "year": 2023, "venue": "ISCA", "citedby": 312},
            {"title": "Hardware Support for Efficient Shared-Memory Multiprocessing", "year": 2022, "venue": "MICRO", "citedby": 198},
            {"title": "Dynamic Energy Management in Embedded Systems", "year": 2022, "venue": "ASPLOS", "citedby": 445},
            {"title": "Architectural Support for Fine-Grained Parallelism", "year": 2021, "venue": "HPCA", "citedby": 267},
            {"title": "Cache Coherence at Scale: Lessons from Production Systems", "year": 2021, "venue": "ISCA", "citedby": 389},
        ],
        "load_max": 15,
    },
    {
        "name": "Onur Mutlu",
        "email": "onur.mutlu@ethz.ch",
        "institution": "ETH Zurich",
        "scholar_url": "https://scholar.google.com/citations?user=omutlu",
        "fetch_status": "done",
        "expertise_topics": ["Memory Systems", "Processing-In-Memory", "DRAM Architecture", "Rowhammer Security"],
        "publications": [
            {"title": "DRAM Rowhammer Attacks and Defenses", "year": 2024, "venue": "ISCA", "citedby": 892},
            {"title": "PIM-Enabled Instructions: A Low-Overhead Architecture for Processing-in-Memory", "year": 2023, "venue": "ISCA", "citedby": 567},
            {"title": "Tiered-Latency DRAM: A Low Latency and Low Cost DRAM Architecture", "year": 2023, "venue": "HPCA", "citedby": 334},
            {"title": "Rethinking DRAM Design and Organization for Energy-Constrained Multi-Cores", "year": 2022, "venue": "ISCA", "citedby": 412},
            {"title": "Memory Access Scheduling for Improved Memory System Utilization", "year": 2021, "venue": "ASPLOS", "citedby": 289},
        ],
        "load_max": 15,
    },
    {
        "name": "Tor Aamodt",
        "email": "aamodt@ece.ubc.ca",
        "institution": "University of British Columbia",
        "scholar_url": "https://scholar.google.com/citations?user=aamodt",
        "fetch_status": "done",
        "expertise_topics": ["GPU Architecture", "Memory Systems", "Hardware Accelerators", "Parallel Computing"],
        "publications": [
            {"title": "GPGPU-Sim: A Detailed GPU Microarchitectural Simulator", "year": 2023, "venue": "ISPASS", "citedby": 1243},
            {"title": "Cache Coherence for GPU Architectures", "year": 2022, "venue": "HPCA", "citedby": 456},
            {"title": "Efficient GPU Register File Design", "year": 2022, "venue": "MICRO", "citedby": 312},
            {"title": "Warped-Compression: Enabling Power Efficient GPUs through Register Compression", "year": 2021, "venue": "ISCA", "citedby": 278},
        ],
        "load_max": 12,
    },
    {
        "name": "Karu Sankaralingam",
        "email": "karu@cs.wisc.edu",
        "institution": "University of Wisconsin-Madison",
        "scholar_url": "https://scholar.google.com/citations?user=karu",
        "fetch_status": "done",
        "expertise_topics": ["Processor Architecture", "Spatial Computing", "Reconfigurable Computing", "Compilers"],
        "publications": [
            {"title": "Spatial Architectures: Past, Present, and Future", "year": 2024, "venue": "ISCA", "citedby": 234},
            {"title": "DySER: Unifying Functionality and Parallelism Specialization for Energy-Efficient Computing", "year": 2023, "venue": "IEEE Micro", "citedby": 567},
            {"title": "TRIPS: Toward Microprocessor Architecture for Terascale Integration", "year": 2022, "venue": "MICRO", "citedby": 489},
        ],
        "load_max": 12,
    },
    {
        "name": "Babak Falsafi",
        "email": "babak.falsafi@epfl.ch",
        "institution": "EPFL",
        "scholar_url": "https://scholar.google.com/citations?user=falsafi",
        "fetch_status": "done",
        "expertise_topics": ["Server Architecture", "Memory Hierarchy", "Data Center Systems", "Cache Coherence"],
        "publications": [
            {"title": "Scale-Out NUMA", "year": 2023, "venue": "ASPLOS", "citedby": 678},
            {"title": "Clearing the Clouds: A Study of Emerging Scale-out Workloads on Modern Hardware", "year": 2022, "venue": "ASPLOS", "citedby": 534},
            {"title": "Coherence Protocol for Transparent Management of Scratchpad Memories", "year": 2022, "venue": "ISCA", "citedby": 289},
            {"title": "Proactive Instruction Fetch", "year": 2021, "venue": "MICRO", "citedby": 345},
        ],
        "load_max": 15,
    },
    {
        "name": "Moinuddin Qureshi",
        "email": "moin@cc.gatech.edu",
        "institution": "Georgia Tech",
        "scholar_url": "https://scholar.google.com/citations?user=mqureshi",
        "fetch_status": "done",
        "expertise_topics": ["Cache Design", "Non-Volatile Memory", "Security Architecture", "Memory Systems"],
        "publications": [
            {"title": "Scalable High Performance Main Memory System Using Phase-Change Memory Technology", "year": 2023, "venue": "ISCA", "citedby": 934},
            {"title": "Adaptive Insertion Policies for High Performance Caching", "year": 2022, "venue": "ISCA", "citedby": 812},
            {"title": "CEASE: A Carbon-Efficient, Application-Sensitive SSD Design", "year": 2022, "venue": "MICRO", "citedby": 267},
            {"title": "Fundamental Latency Trade-offs in Architecting DRAM Caches", "year": 2021, "venue": "MICRO", "citedby": 389},
        ],
        "load_max": 12,
    },
    {
        "name": "Lingjia Tang",
        "email": "lingjia@umich.edu",
        "institution": "University of Michigan",
        "scholar_url": "https://scholar.google.com/citations?user=ltang",
        "fetch_status": "done",
        "expertise_topics": ["Operating Systems", "Virtualization", "Memory Management", "Cloud Computing"],
        "publications": [
            {"title": "Taming Performance Variability in Virtualized Environments", "year": 2023, "venue": "OSDI", "citedby": 445},
            {"title": "Towards Practical Default-On Multi-Core Record and Replay", "year": 2022, "venue": "ASPLOS", "citedby": 312},
            {"title": "Whirlpool: Improving Dynamic Instruction Scheduling with Coloring", "year": 2021, "venue": "ASPLOS", "citedby": 267},
        ],
        "load_max": 10,
    },
    {
        "name": "Carole-Jean Wu",
        "email": "carolejeanwu@meta.com",
        "institution": "Meta AI",
        "scholar_url": "https://scholar.google.com/citations?user=cjwu",
        "fetch_status": "done",
        "expertise_topics": ["Machine Learning Systems", "Sustainable Computing", "Memory Systems", "AI Hardware"],
        "publications": [
            {"title": "Sustainable AI: Environmental Implications, Challenges, and Opportunities", "year": 2024, "venue": "MLSys", "citedby": 1567},
            {"title": "Efficient Deep Learning: A Survey on Making Deep Learning Models Smaller, Faster, and Better", "year": 2023, "venue": "ACM Computing Surveys", "citedby": 2345},
            {"title": "RecNMP: Accelerating Personalized Recommendation with Near-Memory Processing", "year": 2022, "venue": "ISCA", "citedby": 534},
        ],
        "load_max": 10,
    },
    {
        "name": "Natalie Enright Jerger",
        "email": "enright@ece.utoronto.ca",
        "institution": "University of Toronto",
        "scholar_url": "https://scholar.google.com/citations?user=nejjerger",
        "fetch_status": "done",
        "expertise_topics": ["Network-on-Chip", "Interconnection Networks", "Cache Coherence", "Many-Core Architecture"],
        "publications": [
            {"title": "An Introduction to Network-on-Chip Architectures", "year": 2023, "venue": "Synthesis Lectures", "citedby": 1234},
            {"title": "Virtual Circuit Tree Multicasting in a Mesh Network", "year": 2022, "venue": "ISCA", "citedby": 345},
            {"title": "Techniques for Bandwidth-Efficient Prefetching of Linked Data Structures", "year": 2021, "venue": "HPCA", "citedby": 289},
        ],
        "load_max": 12,
    },
    {
        "name": "Timothy Sherwood",
        "email": "sherwood@cs.ucsb.edu",
        "institution": "UC Santa Barbara",
        "scholar_url": "https://scholar.google.com/citations?user=tsherwood",
        "fetch_status": "done",
        "expertise_topics": ["Program Analysis", "Architectural Simulation", "Security", "Embedded Systems"],
        "publications": [
            {"title": "Continual Flow Pipelines", "year": 2022, "venue": "ASPLOS", "citedby": 456},
            {"title": "Basic Block Distribution Analysis to Find Periodic Behavior and Simulation Points", "year": 2021, "venue": "PACT", "citedby": 678},
            {"title": "Reducing Cache Misses Using Hardware and Software Prefetching", "year": 2021, "venue": "ICS", "citedby": 312},
        ],
        "load_max": 10,
    },
    {
        "name": "Hillery Hunter",
        "email": "hhunter@ibm.com",
        "institution": "IBM Research",
        "scholar_url": "https://scholar.google.com/citations?user=hhunter",
        "fetch_status": "done",
        "expertise_topics": ["Non-Volatile Memory", "Storage Systems", "Enterprise Architecture", "Memory Technology"],
        "publications": [
            {"title": "Non-Volatile Memory through an Operational Lens", "year": 2023, "venue": "ISCA", "citedby": 389},
            {"title": "The Storage Hierarchy is Not a Hierarchy: Optimizing Caching on Modern Storage Devices", "year": 2022, "venue": "FAST", "citedby": 512},
            {"title": "DRAMA: Exploiting DRAM Addressing for Cross-CPU Attacks", "year": 2021, "venue": "USENIX Security", "citedby": 445},
        ],
        "load_max": 10,
    },
    {
        "name": "Boris Grot",
        "email": "bgrot@ed.ac.uk",
        "institution": "University of Edinburgh",
        "scholar_url": "https://scholar.google.com/citations?user=bgrot",
        "fetch_status": "needs_confirmation",
        "expertise_topics": ["Interconnects", "Datacenter Architecture", "Memory Bandwidth", "CXL"],
        "publications": [
            {"title": "Hop, Skip, & Jump: Practical On-Stack Replacement for a Cross-Platform Language VM", "year": 2023, "venue": "MICRO", "citedby": 234},
            {"title": "Scalable Network Interfaces for Next-Generation Distributed Platforms", "year": 2022, "venue": "ISCA", "citedby": 312},
        ],
        "load_max": 12,
    },
]

# ── 匹配分数（精心设计，体现合理的专业匹配）────────────────────────────────
# (paper_idx, reviewer_idx, total, topic, method, recency, rationale)
MATCH_SCORES = [
    # MemFlow (0) — 内存系统相关
    (0, 0, 88, 90, 82, 95, "研究方向高度吻合；近 3 年有 2 篇相关 ISCA 发表（含 Cache Coherence at Scale）；技术方法相近"),
    (0, 1, 92, 95, 88, 98, "研究方向高度吻合；近 3 年有 3 篇内存系统顶会发表；技术方法相近"),
    (0, 4, 79, 82, 71, 85, "研究方向部分重叠；近 3 年有 2 篇服务器内存相关发表"),
    (0, 5, 84, 88, 76, 90, "研究方向高度吻合；近 3 年有 NVM 和 Cache 相关发表"),

    # SparsePIM (1) — PIM + 稀疏计算
    (1, 1, 85, 92, 78, 88, "研究方向高度吻合；PIM 方向近 3 年有代表作；技术方法相近"),
    (1, 2, 71, 74, 68, 72, "研究方向部分重叠；GPU 并行计算经验相关"),
    (1, 7, 76, 80, 70, 78, "近 3 年有 RecNMP 相关发表；ML 加速器经验丰富"),

    # TLBshot (2) — 虚拟内存 + OS
    (2, 6, 83, 86, 78, 86, "研究方向高度吻合；操作系统与内存管理方向吻合"),
    (2, 0, 67, 70, 62, 70, "研究方向部分重叠；架构支持虚拟化方向"),
    (2, 9, 61, 65, 55, 62, "程序分析与安全方向部分相关"),

    # Photonic Interconnects (3) — 互联网络
    (3, 8, 74, 78, 68, 76, "网络互联方向吻合；NoC 设计经验相关"),
    (3, 11, 82, 85, 76, 84, "CXL 和数据中心互联方向高度吻合"),
    (3, 7, 69, 72, 65, 70, "数据中心系统方向相关"),

    # RISC-V Genomics (4) — ISA + 领域加速
    (4, 3, 80, 84, 74, 82, "可重构计算与 ISA 扩展方向吻合"),
    (4, 9, 65, 68, 60, 66, "嵌入式系统方向部分相关"),
    (4, 2, 61, 64, 58, 62, "硬件加速器经验相关"),

    # Chronos (5) — 内存一致性 + 推测执行
    (5, 0, 86, 90, 80, 88, "研究方向高度吻合；内存一致性方向近年持续发表"),
    (5, 1, 79, 82, 74, 80, "内存系统和推测执行方向吻合"),
    (5, 3, 74, 78, 68, 76, "处理器架构与推测执行方向相关"),

    # NeuralPrefetch (6) — 预取 + ML
    (6, 5, 83, 87, 77, 85, "Cache 和预取方向高度吻合；非易失内存相关"),
    (6, 7, 80, 84, 74, 82, "ML 系统与硬件结合方向近年代表作"),
    (6, 0, 72, 76, 66, 74, "内存层次设计方向相关"),

    # SafeStack (7) — 安全 + 体系结构
    (7, 9, 85, 89, 79, 87, "安全与程序分析方向高度吻合"),
    (7, 1, 76, 80, 70, 78, "Rowhammer 安全研究背景相关"),
    (7, 10, 70, 74, 64, 72, "NVM 安全方向部分相关"),

    # CXL-Fabric (8) — CXL + HPC
    (8, 11, 91, 94, 86, 94, "CXL 和数据中心内存方向高度吻合；近年代表作"),
    (8, 1, 83, 87, 77, 85, "内存系统方向高度吻合"),
    (8, 4, 79, 83, 73, 81, "服务器架构与内存层次方向吻合"),

    # Thermal 3D (9) — VLSI + 3D 集成
    (9, 3, 68, 72, 62, 70, "可重构计算与芯片设计方向部分相关"),
    (9, 10, 63, 66, 58, 64, "企业级架构与存储系统方向相关"),
]

# ── 利益冲突数据 ────────────────────────────────────────────────────────────
CONFLICTS = [
    # MIT 作者与 Princeton reviewer 同校历史
    {"paper_idx": 0, "reviewer_idx": 3, "source": "coauthor", "detail": "共同发表于 MICRO 2020", "status": "confirmed"},
    # KAIST 论文作者与某 reviewer 同机构
    {"paper_idx": 11, "reviewer_idx": 2, "source": "institution", "detail": "同在 KAIST 任职（2022-2024）", "status": "confirmed"},
    # 自申报
    {"paper_idx": 4, "reviewer_idx": 6, "source": "self_reported", "detail": "合著者为我的前博士生", "status": "pending"},
]


def seed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    # 初始化表
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.models.db import init_db
    init_db()

    print("📄 插入论文...")
    paper_ids = []
    for i, p in enumerate(PAPERS):
        cur = conn.execute(
            """INSERT OR IGNORE INTO papers
               (title, abstract, authors, topics, methods, required_expertise, analysis_status)
               VALUES (?,?,?,?,?,?,?)""",
            (
                p["title"], p["abstract"],
                json.dumps(p["authors"]),
                json.dumps(p["topics"]),
                json.dumps(p["methods"]),
                json.dumps(p["required_expertise"]),
                p["status"],
            ),
        )
        if cur.lastrowid:
            paper_ids.append(cur.lastrowid)
        else:
            row = conn.execute("SELECT id FROM papers WHERE title=?", (p["title"],)).fetchone()
            paper_ids.append(row["id"])
    conn.commit()
    print(f"  ✓ {len(paper_ids)} 篇论文")

    print("👤 插入审稿人...")
    reviewer_ids = []
    for r in REVIEWERS:
        cur = conn.execute(
            """INSERT OR IGNORE INTO reviewers
               (name, email, institution, scholar_url, fetch_status, expertise_topics, publications, load_max)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                r["name"], r["email"], r["institution"], r["scholar_url"],
                r["fetch_status"],
                json.dumps(r["expertise_topics"]),
                json.dumps(r["publications"]),
                r["load_max"],
            ),
        )
        if cur.lastrowid:
            reviewer_ids.append(cur.lastrowid)
        else:
            row = conn.execute("SELECT id FROM reviewers WHERE email=?", (r["email"],)).fetchone()
            reviewer_ids.append(row["id"])
    conn.commit()
    print(f"  ✓ {len(reviewer_ids)} 位审稿人")

    print("🎯 插入匹配分数...")
    count = 0
    for pidx, ridx, total, topic, method, recency, rationale in MATCH_SCORES:
        if pidx >= len(paper_ids) or ridx >= len(reviewer_ids):
            continue
        conn.execute(
            """INSERT OR REPLACE INTO match_scores
               (paper_id, reviewer_id, total_score, topic_score, method_score, recency_score, rationale)
               VALUES (?,?,?,?,?,?,?)""",
            (paper_ids[pidx], reviewer_ids[ridx], total, topic, method, recency, rationale),
        )
        count += 1
    conn.commit()
    print(f"  ✓ {count} 条匹配分数")

    print("⚠️  插入利益冲突...")
    for c in CONFLICTS:
        if c["paper_idx"] >= len(paper_ids) or c["reviewer_idx"] >= len(reviewer_ids):
            continue
        conn.execute(
            """INSERT OR IGNORE INTO conflicts
               (paper_id, reviewer_id, source, detail, status, reported_by)
               VALUES (?,?,?,?,?,'seed_script')""",
            (paper_ids[c["paper_idx"]], reviewer_ids[c["reviewer_idx"]],
             c["source"], c["detail"], c["status"]),
        )
    conn.commit()
    print(f"  ✓ {len(CONFLICTS)} 条 COI 记录")

    print("📋 插入分配结果（前 8 篇论文）...")
    assign_pairs = [
        (0, 0), (0, 1), (0, 5),   # MemFlow → Martonosi, Mutlu, Qureshi
        (1, 1), (1, 2), (1, 7),   # SparsePIM → Mutlu, Aamodt, Wu
        (2, 6), (2, 0), (2, 9),   # TLBshot → Tang, Martonosi, Sherwood
        (3, 8), (3, 11), (3, 7),  # Photonic → Jerger, Grot, Wu
        (4, 3), (4, 9), (4, 2),   # RISC-V → Sankaralingam, Sherwood, Aamodt
        (5, 0), (5, 1), (5, 3),   # Chronos → Martonosi, Mutlu, Sankaralingam
        (6, 5), (6, 7), (6, 0),   # NeuralPrefetch → Qureshi, Wu, Martonosi
        (7, 9), (7, 1), (7, 10),  # SafeStack → Sherwood, Mutlu, Hunter
    ]
    acount = 0
    for pidx, ridx in assign_pairs:
        if pidx >= len(paper_ids) or ridx >= len(reviewer_ids):
            continue
        conn.execute(
            """INSERT OR IGNORE INTO assignments
               (paper_id, reviewer_id, source, status)
               VALUES (?,?,'auto','confirmed')""",
            (paper_ids[pidx], reviewer_ids[ridx]),
        )
        acount += 1
    conn.commit()
    print(f"  ✓ {acount} 对分配")

    conn.close()
    print("\n✅ 演示数据插入完成！")
    print("   运行 ./dev.sh 启动系统查看效果")


if __name__ == "__main__":
    seed()
