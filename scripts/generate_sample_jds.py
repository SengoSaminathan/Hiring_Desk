"""
Generator script for enterprise-grade Job Description (JD) Word documents (.docx)
using Senior_AI_Lead_Job_Description.docx as a visual and typographic template.
"""

import os
import docx
from docx.shared import Pt, RGBColor

BASE_TEMPLATE = "Senior_AI_Lead_Job_Description.docx"

ROLES = [
    {
        "filename": "Senior_Fullstack_Engineer_Job_Description.docx",
        "title": "SENIOR FULLSTACK ENGINEER",
        "tagline": "Fullstack Engineering • React & Next.js • Node.js / Python • Cloud & Distributed Systems",
        "overview": (
            "We are seeking an experienced Senior Fullstack Engineer to drive the end-to-end design, development, "
            "and scaling of mission-critical web applications and distributed backend microservices. In this role, "
            "you will architect resilient cloud-native APIs, build intuitive and responsive user interfaces, establish "
            "software development standards, and lead technical execution across the entire technology stack. You will "
            "work closely with product managers, designers, and platform engineers to deliver high-impact software "
            "solutions that delight users and scale seamlessly under high transactional loads."
        ),
        "responsibilities": [
            {
                "heading": "Fullstack Architecture & Technical Leadership",
                "items": [
                    "Architect, build, and maintain robust, scalable fullstack web applications using modern JavaScript/TypeScript frameworks and backend ecosystems.",
                    "Design and implement secure, high-throughput RESTful and GraphQL APIs, event streams, and background job processing pipelines.",
                    "Establish coding guidelines, lead architectural design sessions, conduct thorough code reviews, and champion engineering best practices across the team.",
                    "Evaluate emerging technologies, frameworks, and third-party tools to modernize technical architecture and accelerate delivery velocity.",
                ],
            },
            {
                "heading": "Backend Services & Distributed Systems",
                "items": [
                    "Design modular microservices with clean separation of concerns, high testability, and automated deployment readiness.",
                    "Model, optimize, and maintain relational (PostgreSQL, MySQL) and NoSQL (MongoDB, Redis) databases with strict consistency and performance budgets.",
                    "Implement asynchronous messaging and event-driven patterns using message brokers (RabbitMQ, Kafka, or AWS SQS).",
                    "Ensure enterprise-grade security, implementing robust authentication/authorization (OAuth2, JWT, RBAC), data encryption, and rate limiting.",
                ],
            },
            {
                "heading": "Frontend Engineering & User Experience",
                "items": [
                    "Develop responsive, accessible, and performant user interfaces using React, Next.js, and modern CSS frameworks.",
                    "Build reusable, modular UI component libraries adhering to design tokens and accessibility (WCAG 2.1) guidelines.",
                    "Optimize client-side performance, Core Web Vitals, bundle sizes, server-side rendering (SSR), and state management (Zustand, React Query).",
                    "Collaborate closely with UI/UX designers to translate wireframes and user journeys into fluid, production-ready web experiences.",
                ],
            },
            {
                "heading": "DevOps, Reliability & Operational Excellence",
                "items": [
                    "Collaborate with DevOps teams to deploy containerized workloads using Docker, Kubernetes, and CI/CD pipelines (GitHub Actions, GitLab CI).",
                    "Instrument distributed tracing, structured logging, and health monitoring using tools such as Datadog, Prometheus, Grafana, and Sentry.",
                    "Participate in on-call rotations, incident retrospectives, root-cause analyses, and proactive technical debt remediation.",
                    "Drive comprehensive automated testing strategies including unit tests (Jest, pytest), integration tests, and end-to-end browser tests (Playwright, Cypress).",
                ],
            },
        ],
        "requirements": [
            "6–10 years of professional fullstack software engineering experience in modern production environments.",
            "Strong proficiency in modern JavaScript/TypeScript, React, and Next.js on the frontend.",
            "Deep expertise in at least one modern backend ecosystem (Node.js/Express/NestJS, Python/FastAPI/Django, or Go).",
            "Demonstrated experience designing, building, and documenting production RESTful APIs and GraphQL endpoints.",
            "Strong hands-on experience with SQL databases (PostgreSQL, MySQL), complex query optimization, indexing, and ORMs (Prisma, SQLAlchemy, TypeORM).",
            "Working experience with caching strategies, distributed session management, and in-memory datastores (Redis).",
            "Solid foundation in computer science fundamentals: algorithms, data structures, concurrency, and distributed system design.",
            "Experience with automated testing frameworks (Jest, React Testing Library, pytest, Playwright) and automated CI/CD pipelines.",
            "Excellent communication, technical documentation, problem-solving, and cross-functional collaboration abilities.",
        ],
        "preferred": [
            "Experience deploying and operating applications on cloud infrastructure (AWS, Microsoft Azure, or GCP).",
            "Familiarity with containerization and orchestration tooling (Docker, Docker Compose, Kubernetes, Helm).",
            "Experience integrating AI/LLM capabilities (OpenAI APIs, LangChain, vector search with pgvector) into customer-facing applications.",
            "Working knowledge of WebSockets, Server-Sent Events (SSE), and real-time collaboration features.",
            "Experience with micro-frontend architectures, monorepo tooling (Turborepo, Nx), and module federation.",
            "Active contributions to open-source software, developer community technical blogs, or architecture talks.",
        ],
        "leadership": [
            "Has owned major software features or entire product surfaces from technical specification to production release and post-launch maintenance.",
            "Proven track record of mentoring junior and mid-level engineers, fostering a culture of technical excellence, empathy, and continuous learning.",
            "Skilled at balancing engineering velocity and pragmatic delivery with code quality, architecture scalability, and security.",
        ],
        "education": "Bachelor’s or Master’s degree in Computer Science, Software Engineering, Information Technology, or equivalent practical experience.",
        "success_measures": [
            "High-availability web applications delivered and scaled to production with sub-200ms p95 API response times.",
            "Zero-defect deployments achieved through automated CI/CD and comprehensive test coverage exceeding 85%.",
            "Measurable acceleration in team velocity through reusable architectural patterns and technical documentation.",
            "Proactive identification and elimination of critical security, latency, and database query bottlenecks.",
        ],
        "additional_info": (
            "Location: Dubai, UAE / Remote options available based on role requirements. Work arrangement: Hybrid or flexible full-time. "
            "Compensation: Competitive enterprise package commensurate with experience, including health coverage and annual performance incentives."
        ),
    },
    {
        "filename": "Lead_UI_Frontend_Engineer_Job_Description.docx",
        "title": "LEAD UI / FRONTEND ENGINEER",
        "tagline": "User Interface Architecture • React & Next.js • Design Systems • Web Performance • Accessibility",
        "overview": (
            "We are looking for a visionary Lead UI / Frontend Engineer to champion frontend architecture, user experience, "
            "and design system engineering across our product portfolio. In this role, you will establish modern frontend "
            "standards, build accessible and reusable component ecosystems, optimize client-side rendering performance, "
            "and partner with product designers and fullstack engineers to create frictionless, enterprise-grade user interfaces. "
            "This position requires deep frontend craftsmanship, eye for visual aesthetics, and strong technical leadership."
        ),
        "responsibilities": [
            {
                "heading": "Frontend Architecture & Technical Strategy",
                "items": [
                    "Define and lead the long-term frontend technical roadmap, framework selection, and client-side architecture.",
                    "Establish frontend engineering standards, component authoring conventions, state management strategies, and code review criteria.",
                    "Oversee migration to modern frontend stacks (React 19, Next.js App Router, Server Components) ensuring modularity and maintainability.",
                    "Optimize developer experience (DX) through modern build tooling (Vite, Turbopack), linters, formatting standards, and automated pre-commit gates.",
                ],
            },
            {
                "heading": "Design System & Component Engineering",
                "items": [
                    "Architect, build, and maintain an enterprise-grade multi-brand Design System in Storybook with Figma Code Connect integration.",
                    "Engineer highly reusable, tokenized UI primitives and complex composite widgets supporting responsive layouts, dark/light themes, and internationalization (i18n).",
                    "Enforce strict accessibility standards (WCAG 2.1 AA compliance), keyboard navigation, ARIA attributes, and screen reader compatibility.",
                    "Bridge the gap between design and engineering, ensuring 100% design fidelity and consistent visual polish across all surfaces.",
                ],
            },
            {
                "heading": "Web Performance & Core Web Vitals",
                "items": [
                    "Measure, monitor, and aggressively optimize Core Web Vitals: LCP (Largest Contentful Paint), INP (Interaction to Next Paint), and CLS (Cumulative Layout Shift).",
                    "Implement intelligent code splitting, lazy loading, route prefetching, image/font optimization, and caching strategies.",
                    "Analyze memory profiles, DOM node counts, render waterfalls, and bundle analyzers to eliminate rendering jank and memory leaks.",
                    "Establish automated performance regression budgets in CI pipelines to prevent latency bloat before production releases.",
                ],
            },
            {
                "heading": "Mentorship, Collaboration & Cross-Functional Alignment",
                "items": [
                    "Directly mentor frontend engineers across product pods, conducting architecture pairing, design critiques, and technical workshops.",
                    "Partner closely with Product Managers and UX Researchers to evaluate user interactions, validate prototypes, and iterate based on user analytics.",
                    "Collaborate with backend teams on contract-first API design (OpenAPI, tRPC, GraphQL) to ensure optimal frontend data fetching efficiency.",
                ],
            },
        ],
        "requirements": [
            "7–11 years of dedicated frontend and user interface engineering experience in modern SaaS or web platform environments.",
            "Mastery of modern JavaScript/TypeScript, React, Next.js, and modern CSS paradigms (Tailwind CSS, CSS Modules, CSS-in-JS).",
            "Proven track record architecting and maintaining production Design Systems or widely adopted UI component libraries.",
            "Deep understanding of browser rendering pipelines, event loops, DOM diffing, hydration cycles, and client-side caching.",
            "Extensive experience with state management libraries and data synchronization tools (React Query/TanStack, Zustand, Redux Toolkit).",
            "Strong commitment to web accessibility standards (WCAG 2.1 AA/AAA) and hands-on experience with assistive technology testing.",
            "Hands-on experience with frontend testing suites (Jest, Vitest, React Testing Library, Cypress, Playwright) and visual regression testing (Chromatic, Percy).",
            "Exceptional portfolio or demonstration of crafted, intuitive, responsive, and visually stunning web applications.",
        ],
        "preferred": [
            "Experience building AI-powered user interfaces: streaming chat interfaces, generative UI components, headed automation views, and markdown renderers.",
            "Experience with micro-frontend architectures, module federation, and web workers for heavy background client computation.",
            "Familiarity with interactive data visualization and charting libraries (D3.js, Chart.js, Recharts, Canvas, WebGL).",
            "Knowledge of mobile-responsive web development, Progressive Web Apps (PWA), and cross-browser rendering quirks.",
            "Experience working with Figma plugins, design tokens (Style Dictionary), and design-to-code workflows.",
        ],
        "leadership": [
            "Proven technical leadership guiding engineering teams through complex frontend refactors with zero customer disruption.",
            "Passionate advocate for user empathy, visual polish, and technical craftsmanship.",
            "Ability to articulate complex architectural decisions and trade-offs clearly to designers, engineers, and executives.",
        ],
        "education": "Bachelor’s or Master’s degree in Computer Science, Software Engineering, Human-Computer Interaction (HCI), Design, or equivalent practical experience.",
        "success_measures": [
            "Enterprise Design System adopted across 100% of product feature teams with documented component coverage.",
            "Core Web Vitals scores maintained above 95 across all primary product flows.",
            "Frontend release lead time and bug regression rates cut by over 30% through automated testing and component reuse.",
            "High satisfaction scores in developer experience (DX) and UX design consistency surveys.",
        ],
        "additional_info": (
            "Location: Dubai, UAE / Hybrid / Remote. Work arrangement: Full-time. "
            "Compensation: Attractive enterprise compensation package, generous learning allowance, and comprehensive benefits."
        ),
    },
    {
        "filename": "Senior_DevOps_Cloud_Engineer_Job_Description.docx",
        "title": "SENIOR CLOUD & DEVOPS ENGINEER",
        "tagline": "Cloud Infrastructure • Kubernetes • Terraform • CI/CD Automation • SRE & Observability",
        "overview": (
            "We are seeking an accomplished Senior Cloud & DevOps Engineer to design, automate, and scale our enterprise "
            "cloud infrastructure, container platforms, and deployment pipelines. In this role, you will be the backbone "
            "of our reliability and deployment velocity, managing Infrastructure as Code (IaC), multi-region Kubernetes clusters, "
            "automated CI/CD workflows, zero-trust cloud security, and comprehensive observability stacks. You will work at "
            "the intersection of software engineering and systems operations to ensure maximum uptime, security, and developer productivity."
        ),
        "responsibilities": [
            {
                "heading": "Infrastructure as Code & Cloud Architecture",
                "items": [
                    "Design, provision, and maintain secure, multi-tier cloud infrastructure on AWS and Azure using Terraform / OpenTofu.",
                    "Establish standardized, modular IaC modules, versioning policies, state management backends, and automated drift detection.",
                    "Architect multi-region, highly available networking topologies: VPCs, subnets, transit gateways, VPNs, NAT gateways, and DNS routing.",
                    "Implement cloud FinOps practices: resource tagging, right-sizing, spot instance utilization, and automated cost optimization.",
                ],
            },
            {
                "heading": "Container Orchestration & Kubernetes Management",
                "items": [
                    "Manage, configure, and upgrade production-grade managed Kubernetes clusters (Amazon EKS, Azure AKS) with zero downtime.",
                    "Deploy and optimize ingress controllers, service meshes (Istio/Linkerd), network policies, storage classes, and cluster autoscalers (Karpenter).",
                    "Maintain Helm charts, Kustomize overlays, and GitOps workflows using ArgoCD or Flux for automated cluster configuration.",
                    "Configure compute and GPU node groups to support high-throughput microservices and AI/ML model inference workloads.",
                ],
            },
            {
                "heading": "CI/CD Automation & Developer Velocity",
                "items": [
                    "Design and maintain scalable CI/CD pipelines (GitHub Actions, GitLab CI) enabling safe, automated multi-stage promotions.",
                    "Implement advanced deployment strategies: Blue/Green deployments, Canary rollouts, and automated health-check rollbacks.",
                    "Automate container image builds, vulnerability scanning (Trivy, Snyk), SBOM generation, and artifact registry management.",
                    "Empower product engineering teams with self-service preview environments, ephemeral test databases, and rapid feedback loops.",
                ],
            },
            {
                "heading": "Security, Reliability & Observability (SRE)",
                "items": [
                    "Implement the Site Reliability Engineering (SRE) framework: define SLIs, SLOs, error budgets, and automated incident escalation paths.",
                    "Deploy and tune centralized observability stacks: Prometheus, Grafana, OpenTelemetry, Datadog, and ELK / OpenSearch.",
                    "Enforce zero-trust security postures: IAM least-privilege, KMS secrets rotation, HashiCorp Vault, and cloud compliance standards (SOC2, ISO 27001).",
                    "Lead disaster recovery (DR) simulations, backup verification, chaos engineering exercises, and blameless post-mortem reviews.",
                ],
            },
        ],
        "requirements": [
            "6–10 years of experience in DevOps, Cloud Engineering, Platform Engineering, or Site Reliability Engineering (SRE).",
            "Deep hands-on experience provisioning enterprise infrastructure on AWS (EKS, RDS, S3, CloudFront, IAM) or Microsoft Azure (AKS, Azure SQL).",
            "Expert-level proficiency with Terraform / OpenTofu for infrastructure automation and configuration management.",
            "Strong production experience deploying, securing, and maintaining multi-tenant Kubernetes clusters and containerized microservices.",
            "Proven track record building and managing production CI/CD pipelines with GitHub Actions, GitLab CI, or Jenkins.",
            "Strong scripting and systems programming skills in Python, Bash, or Go.",
            "Hands-on expertise implementing centralized monitoring, metrics alerting, and distributed tracing (Prometheus, Grafana, Datadog, Sentry).",
            "Solid networking fundamentals: TCP/IP, DNS, TLS/SSL certificates, HTTP/2, reverse proxies (NGINX, Traefik), and firewall rules.",
            "Demonstrated experience with cloud security, secret management, identity governance, and compliance auditing.",
        ],
        "preferred": [
            "Official cloud or Kubernetes certifications: AWS Certified Solutions Architect Professional, CKA (Certified Kubernetes Administrator), or CKS.",
            "Experience deploying and operating AI/ML infrastructure: GPU node pools, Triton Inference Server, vLLM, and Ollama model runtimes.",
            "Experience with GitOps methodologies and tools (ArgoCD, Argo Rollouts, FluxCD).",
            "Knowledge of database administration and automated failover for PostgreSQL, Redis, and message queues (Kafka, RabbitMQ).",
            "Experience implementing automated compliance scanning and security posture management (CSPM).",
        ],
        "leadership": [
            "Has led cloud infrastructure migrations or platform modernization programs with zero planned downtime.",
            "Fosters a proactive SRE culture of blameless post-mortems, automation over toil, and continuous operational improvement.",
            "Skilled at partnering with software engineering leads to resolve deployment bottlenecks and optimize cloud expenditures.",
        ],
        "education": "Bachelor’s degree in Computer Science, Information Technology, Computer Engineering, or equivalent technical experience.",
        "success_measures": [
            "Achieved 99.95%+ platform uptime across all customer-facing microservices.",
            "Deployment cycle times reduced to under 15 minutes from commit to production.",
            "Zero high-severity security vulnerabilities in cloud infrastructure or container registries.",
            "Cloud infrastructure expenditure reduced by 20–30% through automated rightsizing and FinOps governance.",
        ],
        "additional_info": (
            "Location: Dubai, UAE / Regional Hub / Remote. Work arrangement: Full-time. "
            "Compensation: Highly competitive tax-free salary, comprehensive health and life coverage, and annual bonus scheme."
        ),
    },
    {
        "filename": "Data_Analyst_BI_Specialist_Job_Description.docx",
        "title": "DATA ANALYST & BUSINESS INTELLIGENCE SPECIALIST",
        "tagline": "Business Intelligence • Advanced SQL • Python Analytics • Power BI & Tableau • Data Warehousing",
        "overview": (
            "We are seeking an analytical, business-focused Data Analyst & Business Intelligence (BI) Specialist to transform "
            "complex raw organizational data into actionable strategic insights, executive dashboards, and automated reporting systems. "
            "In this role, you will partner directly with business leaders across HR, Finance, Operations, and Product Engineering "
            "to define KPIs, optimize SQL data pipelines, build scalable semantic models, and uncover growth opportunities through "
            "rigorous exploratory analysis. The ideal candidate pairs technical data engineering strength with strong commercial acumen."
        ),
        "responsibilities": [
            {
                "heading": "Business Intelligence & Executive Dashboards",
                "items": [
                    "Design, build, and maintain interactive, high-impact dashboards and analytical reports in Power BI and Tableau for executive leadership.",
                    "Develop robust semantic data models (star schemas, snowflake schemas) with complex DAX measures and Power Query ETL transformations.",
                    "Automate recurring business reporting workflows, replacing manual spreadsheets with scheduled, real-time data visualisations.",
                    "Conduct design reviews with business stakeholders to ensure dashboard clarity, intuitive drill-downs, and actionable insights.",
                ],
            },
            {
                "heading": "Advanced SQL & Analytics Engineering",
                "items": [
                    "Write complex, highly optimized SQL queries (CTEs, window functions, recursive joins, partitions) across massive enterprise datasets.",
                    "Collaborate with data engineers to model, transform, and clean raw data using dbt (data build tool) and cloud data warehouses.",
                    "Query and aggregate data from cloud warehouses (Snowflake, Google BigQuery, AWS Redshift, or Databricks Lakehouse).",
                    "Conduct rigorous data validation and reconciliation to ensure 100% data integrity, consistency, and audit readiness.",
                ],
            },
            {
                "heading": "Exploratory Analysis & Business Discovery",
                "items": [
                    "Perform deep-dive exploratory data analysis using Python (Pandas, NumPy, Matplotlib) to identify trends, outliers, and correlations.",
                    "Design and analyze A/B tests, cohort retention studies, customer funnel conversion metrics, and workforce sourcing funnels.",
                    "Translate ambiguous business questions into structured analytical frameworks, hypotheses, and empirical recommendations.",
                    "Present findings and strategic data narratives to cross-functional executives through compelling presentations and written briefs.",
                ],
            },
            {
                "heading": "Data Governance, Quality & Stakeholder Enablement",
                "items": [
                    "Establish standardized data dictionaries, metric definitions, and documentation to maintain a trusted Single Source of Truth (SSOT).",
                    "Implement data quality monitoring, automated anomaly detection, and schema validation alerts.",
                    "Conduct training sessions and author self-service guidance to empower business users to explore reports independently.",
                    "Ensure full compliance with enterprise data privacy standards, GDPR, role-based data access (RLS), and confidential employee policies.",
                ],
            },
        ],
        "requirements": [
            "4–8 years of professional experience as a Data Analyst, BI Developer, or Analytics Engineer in a data-driven enterprise.",
            "Advanced SQL expertise: extensive experience writing, profiling, and optimizing complex SQL queries across large data volumes.",
            "Demonstrated mastery of Power BI (DAX, Power Query, Tabular Editor) or Tableau for enterprise-grade dashboard architecture.",
            "Strong Python proficiency for data analysis, manipulation, and statistical visualization (Pandas, NumPy, Seaborn, Jupyter).",
            "Hands-on experience working with modern cloud data platforms (Snowflake, BigQuery, Redshift, PostgreSQL, or Databricks).",
            "Solid grounding in data warehouse modeling: dimensional modeling, Kimball methodology, star schemas, fact and dimension tables.",
            "Proven ability to articulate business metrics, formulate data stories, and influence executive decisions with quantitative evidence.",
            "Meticulous attention to detail with an uncompromising focus on data accuracy and validation.",
        ],
        "preferred": [
            "Experience with dbt (data build tool) for transformed analytics engineering in Git workflows.",
            "Experience with workflow orchestrators such as Apache Airflow, Prefect, or Dagster.",
            "Familiarity with HR analytics, candidate sourcing metrics, sales funnels, or subscription SaaS metrics (ARR, CAC, Churn, LTV).",
            "Exposure to AI-assisted analytics tools (natural language query generation, automated insight summarization using LLMs).",
            "Relevant certifications: Microsoft Certified Power BI Data Analyst (PL-300), Snowflake SnowPro Core, or Tableau Certified Desktop Specialist.",
        ],
        "leadership": [
            "Acts as a trusted analytical advisor to business unit leaders, translating strategic goals into measurable operational KPIs.",
            "Self-starter with strong prioritization skills, capable of managing multiple concurrent analytics deliverables under tight timelines.",
            "Advocate for a data-literate organizational culture through patience, clarity, and hands-on stakeholder coaching.",
        ],
        "education": "Bachelor’s or Master’s degree in Data Analytics, Statistics, Computer Science, Economics, Mathematics, Engineering, or a related quantitative field.",
        "success_measures": [
            "Single source of truth BI dashboards launched and adopted by senior leadership across primary departments.",
            "Manual reporting effort reduced by over 70% through automated ETL pipelines and scheduled refreshes.",
            "Actionable insights delivered that directly improved operational efficiency, hiring funnel conversion, or revenue metrics.",
            "High stakeholder satisfaction ratings and active daily/weekly dashboard engagement metrics.",
        ],
        "additional_info": (
            "Location: Dubai, UAE / Hybrid / On-site. Work arrangement: Full-time. "
            "Compensation: Competitive tax-free salary, healthcare coverage, annual performance bonus, and professional development support."
        ),
    },
    {
        "filename": "Senior_Product_Manager_AI_SaaS_Job_Description.docx",
        "title": "SENIOR PRODUCT MANAGER (AI & ENTERPRISE SAAS)",
        "tagline": "Product Strategy • Enterprise SaaS • AI & Agentic Workflows • Customer Discovery • Agile Delivery",
        "overview": (
            "We are seeking an entrepreneurial Senior Product Manager to lead product discovery, strategic roadmapping, and "
            "feature delivery for our next-generation enterprise AI platform. In this role, you will be the bridge between "
            "cutting-edge AI research, software engineering, customer user experience, and business strategy. You will translate "
            "complex business workflows into intuitive, AI-assisted products, defining product requirements (PRDs), prioritizing "
            "backlogs, conducting user research, and partnering with cross-functional teams to deliver measurable enterprise value."
        ),
        "responsibilities": [
            {
                "heading": "Product Vision, Strategy & Roadmapping",
                "items": [
                    "Define and own the end-to-end product vision, quarterly roadmap, and strategic goals for enterprise AI workflows and automation tools.",
                    "Identify high-impact opportunities where artificial intelligence, LLM agents, and automation solve painful customer problems.",
                    "Conduct competitive market analyses, industry benchmarking, and pricing/packaging assessments to position the product effectively.",
                    "Establish clear product success metrics (OKRs, KPIs), adoption goals, retention benchmarks, and customer value indicators.",
                ],
            },
            {
                "heading": "Customer Discovery & Problem Validation",
                "items": [
                    "Conduct continuous qualitative customer interviews, usability testing, and onsite discovery workshops with enterprise stakeholders.",
                    "Analyze product analytics, user interaction funnels, drop-off points, and feature telemetry using tools such as Mixpanel, Amplitude, or PostHog.",
                    "Synthesize customer feedback and feature requests into clear problem statements, user personas, and prioritized user stories.",
                    "Balance immediate customer commitments with long-term platform scalability and strategic product differentiation.",
                ],
            },
            {
                "heading": "Cross-Functional Execution & Agile Delivery",
                "items": [
                    "Author comprehensive Product Requirement Documents (PRDs), wireframes, acceptance criteria, and edge-case documentation.",
                    "Partner daily with engineering leads, AI engineers, and UI/UX designers in an agile Scrum environment to sprint and deliver iteratively.",
                    "Evaluate technical feasibility, trade-offs, and accuracy versus latency considerations alongside AI/ML architects.",
                    "Drive user acceptance testing (UAT), dogfooding programs, and structured beta testing to validate releases before general availability.",
                ],
            },
            {
                "heading": "Go-to-Market, Enablement & Continuous Improvement",
                "items": [
                    "Partner with Product Marketing, Sales, and Customer Success to author release notes, sales enablement materials, and onboarding flows.",
                    "Monitor post-launch adoption, customer feedback loops, support tickets, and feature engagement to drive rapid iterative enhancements.",
                    "Champion Responsible AI practices, data privacy governance, transparency, and human-in-the-loop review mechanisms.",
                ],
            },
        ],
        "requirements": [
            "5–9 years of product management experience in B2B SaaS, enterprise software, or technical developer platforms.",
            "At least 2 years of hands-on experience managing AI/ML features, LLM workflows, conversational assistants, or workflow automation products.",
            "Demonstrated track record of launching successful zero-to-one enterprise products or significantly scaling existing SaaS platforms.",
            "Strong grasp of modern AI capabilities and trade-offs: prompt engineering, RAG, agentic tool-use, embeddings, and model latency/cost profiles.",
            "Exceptional analytical skills: proficiency with product telemetry tools (Mixpanel, Amplitude), SQL, and quantitative experiment design.",
            "Superb written and verbal communication skills, with the ability to influence cross-functional teams and present persuasively to executive clients.",
            "Strong experience leading agile delivery teams (Scrum, Kanban), backlog grooming, sprint planning, and release retrospectives.",
        ],
        "preferred": [
            "Technical background: Bachelor's degree in Computer Science or previous experience as a software engineer, data scientist, or technical solutions architect.",
            "Experience building HR technology, applicant tracking systems (ATS), recruitment intelligence, or CRM platforms.",
            "Familiarity with enterprise procurement requirements: SOC2 compliance, role-based permissions, data tenancy, and audit trails.",
            "Experience designing AI human-in-the-loop validation experiences and confidence score indicators.",
            "Master of Business Administration (MBA) or relevant professional certifications (Pragmatic Institute, AIPMM).",
        ],
        "leadership": [
            "Relentless customer champion with deep empathy for end-user frustrations and enterprise operational workflows.",
            "Comfortable navigating ambiguity, making data-driven decisions under uncertainty, and managing multiple high-priority initiatives.",
            "Inspiring communicator who rallies cross-functional engineering, design, and sales teams around a unified mission.",
        ],
        "education": "Bachelor’s degree in Computer Science, Business, Engineering, Information Systems, or equivalent practical experience. MBA is an advantage.",
        "success_measures": [
            "Shipped quarterly AI roadmap deliverables on schedule with high feature adoption and customer satisfaction scores (NPS > 50).",
            "Achieved a 35%+ increase in daily active workflow engagement through intuitive automation and agent assistance.",
            "Customer churn reduced and enterprise net retention rate (NRR) improved through high-value product enhancements.",
            "Seamless collaboration and high engagement ratings within the dedicated cross-functional engineering and design pod.",
        ],
        "additional_info": (
            "Location: Dubai, UAE / Regional Hub / Hybrid. Work arrangement: Full-time. "
            "Compensation: Competitive executive package, performance-linked equity/bonus incentives, health and life insurance."
        ),
    },
]


def create_job_description_docx(role_def: dict, output_path: str):
    """Creates a stylized Word document using the Senior AI Lead template formatting."""
    # Load base template to inherit exact font tables, color palettes, and Word styles
    doc = docx.Document(BASE_TEMPLATE)

    # Remove template default paragraphs
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)

    # 1. Main Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run(role_def["title"])
    r_title.bold = True
    r_title.font.name = "Aptos Display"
    r_title.font.size = Pt(25)
    r_title.font.color.rgb = RGBColor(0x21, 0x1B, 0x3A)
    p_title.paragraph_format.space_after = Pt(2)

    # 2. Tagline / Subtitle
    p_tag = doc.add_paragraph()
    r_tag = p_tag.add_run(role_def["tagline"])
    r_tag.font.name = "Aptos"
    r_tag.font.size = Pt(10)
    r_tag.font.color.rgb = RGBColor(0x5F, 0x57, 0x7D)
    p_tag.paragraph_format.space_after = Pt(14)

    # 3. Role Overview
    doc.add_heading("Role Overview", level=1)
    p_overview = doc.add_paragraph(role_def["overview"])
    p_overview.paragraph_format.space_after = Pt(10)

    # 4. Key Responsibilities
    doc.add_heading("Key Responsibilities", level=1)
    for resp in role_def["responsibilities"]:
        doc.add_heading(resp["heading"], level=2)
        for item in resp["items"]:
            doc.add_paragraph(item, style="List Bullet")

    # 5. Required Skills & Qualifications
    doc.add_heading("Required Skills & Qualifications", level=1)
    for req in role_def["requirements"]:
        doc.add_paragraph(req, style="List Bullet")

    # 6. Preferred Skills & Technologies
    doc.add_heading("Preferred Skills & Technologies", level=1)
    for pref in role_def["preferred"]:
        doc.add_paragraph(pref, style="List Bullet")

    # 7. Experience & Leadership Expectations
    doc.add_heading("Experience & Leadership Expectations", level=1)
    for exp in role_def["leadership"]:
        doc.add_paragraph(exp, style="List Bullet")

    # 8. Education
    doc.add_heading("Education", level=1)
    doc.add_paragraph(role_def["education"])

    # 9. Success Measures (First 6–12 Months)
    doc.add_heading("Success Measures (First 6–12 Months)", level=1)
    for sm in role_def["success_measures"]:
        doc.add_paragraph(sm, style="List Bullet")

    # 10. Additional Information
    doc.add_heading("Additional Information", level=1)
    doc.add_paragraph(role_def["additional_info"])

    doc.save(output_path)
    print(f"Generated: {output_path} ({os.path.getsize(output_path):,} bytes)")


def main():
    print(f"Generating {len(ROLES)} enterprise Job Description Word documents...")
    for role in ROLES:
        out_path = role["filename"]
        create_job_description_docx(role, out_path)
    print("All Job Description Word documents successfully generated!")


if __name__ == "__main__":
    main()

