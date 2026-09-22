/**
 * Mock data fixtures for Project Dash headless UX unit tests.
 * Standardized across Project Monaro & Project Aurora schemas.
 */

export const mockConfig = {
  project: {
    slug: "sample",
    name: "Project Aurora",
    title: "Enterprise AI & Sovereign Cloud Modernization",
    organization: "Global Enterprise Transformation Board",
    logoIcon: "🛡️",
    heroTag: "Enterprise Sovereign Enclave • AI Platform Modernization",
    primaryRegisterName: "Joint Program Register",
    secondaryRegisterName: "Team Cloud Register",
    links: {
      charter: "https://example.com/aurora/charter",
      architecture: "https://example.com/aurora/architecture",
      tracker: "https://example.com/aurora/jira"
    }
  },
  kpiPillars: [
    {
      id: "commercial",
      label: "Commercial & Budget",
      value: "🟢 ON TRACK",
      subtext: "Milestone payments aligned"
    },
    {
      id: "milestone",
      label: "Milestone Gate 2",
      value: "🟡 IN PROGRESS",
      subtext: "System review on critical path"
    }
  ],
  sources: {
    googleSheets: { enabled: false, sheetUrl: "" },
    googleDrive: {
      enabled: false,
      folderId: "sample-drive-folder",
      knownReports: [
        {
          id: "rep-w30",
          week: "Week 30",
          date: "28 Aug 2026",
          name: "Weekly Reporting - Week 30 - 28 Aug 2026.pdf",
          url: "https://example.com/drive/rep-w30"
        }
      ]
    },
    geminiNotebooks: { enabled: false, notebookIds: [] }
  },
  features: {
    executiveBriefing: { enabled: true },
    riskMatrix: { enabled: true },
    secondaryRegister: { enabled: true },
    driverTree: { enabled: true },
    timeMachine: { enabled: true },
    podcastAudio: { enabled: true },
    blueprintKnowledge: { enabled: true }
  }
};

export const mockRisks = [
  {
    id: "RSK-001",
    title: "Sovereign HSM Key Attestation Latency Exceeds SLA",
    category: "Security & Sovereign Governance",
    sourceRegister: "joint_program",
    inherentLikelihood: 4,
    inherentConsequence: 5,
    inherentRiskScore: 20,
    residualLikelihood: 3,
    residualConsequence: 3,
    residualRiskScore: 9,
    status: "Active",
    owner: "Security Architecture",
    treatmentStrategy: "Mitigate",
    description: "Cloud HSM multi-region replication delay could impact cryptographic attestation.",
    actionPlan: "Deploy Dedicated HSM partitions with regional active-active caching.",
    blueprintRefs: ["SEC-001", "HSM-002"],
    subPackageBundle: "Bundle A",
    gapPlan: "Complete regional cache deployment by W32."
  },
  {
    id: "RSK-002",
    title: "Regulatory Compliance Audit Gate Staging Delay",
    category: "Regulatory & Compliance",
    sourceRegister: "joint_program",
    inherentLikelihood: 5,
    inherentConsequence: 4,
    inherentRiskScore: 20,
    residualLikelihood: 2,
    residualConsequence: 4,
    residualRiskScore: 8,
    status: "Active",
    owner: "Compliance Team",
    treatmentStrategy: "Mitigate",
    description: "Audit artifacts packaging backlog across third-party security assessments.",
    actionPlan: "Automate evidence collection pipeline.",
    blueprintRefs: ["COMP-003"],
    subPackageBundle: "Bundle B",
    gapPlan: "Integrate automated compliance checks."
  },
  {
    id: "TG-RSK-001",
    title: "Dedicated Interconnect Bandwidth Provisioning Lead Time",
    category: "Infrastructure & Platform Engineering",
    sourceRegister: "team_google",
    inherentLikelihood: 3,
    inherentConsequence: 4,
    inherentRiskScore: 12,
    residualLikelihood: 2,
    residualConsequence: 2,
    residualRiskScore: 4,
    status: "Open",
    owner: "Network Operations",
    treatmentStrategy: "Mitigate",
    description: "Cross-connect fiber delivery timeline in Melbourne DC exceeds 6 weeks.",
    actionPlan: "Engage secondary carrier for expedited 100G cross-connect.",
    blueprintRefs: ["NET-004"],
    subPackageBundle: "Bundle A"
  }
];

export const mockIssues = [
  {
    id: "ISS-001",
    title: "Hardware Appliance Shipping Hold at Customs",
    category: "Procurement & Logistics",
    priority: "P1",
    status: "Open",
    owner: "Logistics Lead",
    description: "Import clearance documentation delay for dedicated encryption units.",
    actionPlan: "Escalate with Australian Border Force broker for expedited release.",
    blueprintRef: "LOG-001"
  }
];

export const mockSnapshots = {
  lastSynced: "2026-09-20T10:00:00Z",
  snapshots: {
    w26: {
      weekNumber: 26,
      week: "Week 26",
      weekLabel: "Week 26",
      date: "2026-07-24",
      activeRisksCount: 42,
      criticalRisksCount: 8,
      audioUrl: "assets/podcast_w26.mp3",
      plans: [],
      top3: [],
      sleeperOutlier: { title: "HSM latency", warning: "Potential jitter" },
      synthesis: { executive: "Summary W26" },
      podcastDialogue: [
        { speaker: "Alex", text: "Welcome to the Week 26 executive risk briefing." },
        { speaker: "Jordan", text: "Today we review sovereign enclave controls." }
      ]
    },
    w27: {
      weekNumber: 27,
      week: "Week 27",
      weekLabel: "Week 27",
      date: "2026-07-31",
      activeRisksCount: 40,
      criticalRisksCount: 7,
      audioUrl: null,
      plans: [
        {
          id: "GP-1",
          ref: "1.13",
          title: "Milestone 2 IBR Alignment",
          owner: "Joint PMO",
          status: "AMBER",
          detail: "Schedule buffer compressed."
        }
      ],
      top3: [],
      sleeperOutlier: { title: "Interconnect lead time", warning: "Cross-connect backlog" },
      synthesis: { executive: "Summary W27" },
      podcastDialogue: [
        { speaker: "Alex", text: "Executive update for Week 27." },
        { speaker: "Jordan", text: "Focusing on hardware procurement and audit prep." }
      ]
    },
    w30: {
      weekNumber: 30,
      week: "Week 30",
      weekLabel: "Week 30",
      date: "2026-08-21",
      activeRisksCount: 35,
      criticalRisksCount: 4,
      isLatest: true,
      audioUrl: null,
      plans: [],
      top3: [],
      sleeperOutlier: { title: "Model quantization", warning: "Latency spikes under load" },
      synthesis: { executive: "Summary W30" },
      podcastDialogue: [
        { speaker: "Alex", text: "Welcome to Week 30. Significant risk burn down observed." },
        { speaker: "Jordan", text: "Key milestones achieved across sovereign security architecture." }
      ]
    }
  }
};

export const mockDriverTree = [
  {
    id: "dt-1",
    title: "Program Delivery Assurance",
    level: 1,
    children: [
      {
        id: "dt-1-1",
        title: "Sovereign AI Security",
        level: 2,
        status: "Amber"
      }
    ]
  }
];

export const mockKnowledge = {
  bundles: [
    {
      id: "Bundle A",
      name: "Sovereign Infrastructure & Networking",
      description: "Foundational hardware, interconnects, and HSM enclaves."
    }
  ]
};
