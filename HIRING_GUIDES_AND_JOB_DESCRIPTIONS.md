# Hiring Guides & Job Descriptions

## Executive Summary

Complete hiring framework for scaling PyRoboSimulator from 2 → 50+ engineers over 30 months. Includes 15 detailed job descriptions, interview rubrics, compensation bands, and onboarding playbooks.

**Timeline:**
- Phase 0 (Now): 2 people (Founder/CTO + Lead Eng)
- Phase 1 (Month 4): +4 (3 eng + PM + Sales)
- Phase 2-3 (Month 12): +12 (8 eng + PM/Design + Sales/Marketing + Ops)
- Phase 4 (Month 22): 30 total
- Phase 5+ (Year 2): 50+ people

---

## Part 1: Compensation Framework

### Salary Bands (US, Series A Context)

| Level | Title | Base | Stock (%) | Sign-On | Total |
|-------|-------|------|-----------|---------|-------|
| L3 | Junior Engineer | $130k | 0.05% | $20k | $150k |
| L4 | Mid Engineer | $160k | 0.10% | $25k | $185k |
| L5 | Senior Engineer | $200k | 0.15% | $30k | $230k |
| L6 | Staff Engineer | $250k | 0.25% | $40k | $290k |
| L7 | Principal | $300k | 0.50% | $50k | $350k |
| P3 | Product Manager | $170k | 0.12% | $25k | $195k |
| P4 | Senior PM | $220k | 0.20% | $35k | $255k |

**Equity Notes:**
- Vesting: 4-year schedule, 1-year cliff
- Strike price: Fair Market Value (FMV) at grant
- Refresh grants at L5+ (annually, 25% of original)
- No acceleration for Series A/B/C

**Benefits (all levels):**
- Health: Medical, dental, vision (100% company paid)
- 401(k): 4% match
- Time off: Unlimited PTO + 10 company holidays
- Learning: $5k/year professional development
- Equipment: MacBook Pro (your choice), monitor, peripherals
- Remote: Remote-first, optional office access

---

## Part 2: Job Descriptions

### Engineering Roles

#### L5 Senior Backend Engineer (City Generation & Simulation)

**Level:** L5 (Senior, 5+ years)  
**Reports to:** VP Engineering  
**Compensation:** $200k + 0.15% equity + $30k sign-on  

**Role Summary:**
Lead backend architecture for city generation, traffic simulation, and agent spawning systems. Own the simulation loop performance and scalability to 100K+ agents.

**Key Responsibilities:**
- Design & implement procedural city generation (L-Systems, Voronoi)
- Architect traffic simulation with A* pathfinding
- Optimize simulation loop for throughput (target: 100K agents/sec)
- Lead PostgreSQL schema design & optimization
- Mentor L3-L4 engineers on simulation architecture
- Drive performance profiling & optimization initiatives

**Requirements:**
- 5+ years backend engineering (Python, Go, or Rust)
- Strong systems thinking & performance optimization
- Experience with spatial data structures (quadtrees, grids)
- Published code samples or portfolio
- Experience leading technical designs

**Nice-to-have:**
- Game engine experience (Unity, Unreal)
- Robotics simulation background
- Kubernetes deployment experience
- ML/AI systems (agents, learning)

**Interview Process:**
1. **Phone Screen (30 min):** Background, motivation, technical breadth
2. **Take-home (4-6 hours):** Implement A* pathfinding + traffic simulation
3. **Architecture (2 hours):** Design city generation system, scale to 1M agents
4. **System Design (1.5 hours):** Database schema for 100M events/day
5. **Culture Fit (1 hour):** Team dynamics, collaboration, growth mindset

**Success Metrics (6 months):**
- City generation library production-ready
- Traffic simulation handling 10K vehicles without degradation
- Database optimized for < 100ms query latency (p99)
- 2+ junior engineers onboarded & productive

---

#### L4 Mid Backend Engineer (Database & Streaming)

**Level:** L4 (Mid, 3-4 years)  
**Reports to:** Senior Backend Engineer  
**Compensation:** $160k + 0.10% equity + $25k sign-on  

**Role Summary:**
Own database layer, caching strategy, and real-time event streaming for simulations.

**Key Responsibilities:**
- Design PostgreSQL schemas for event storage (100M+ events/day)
- Implement Redis caching layer & invalidation strategy
- Build Kafka/RabbitMQ consumer for event processing
- Optimize query performance (p99 < 100ms)
- Write comprehensive database tests & migration scripts
- Document schema changes & architectural decisions

**Requirements:**
- 3+ years backend engineering
- Strong SQL & database optimization skills
- Experience with event streaming (Kafka, RabbitMQ)
- Cache design & Redis
- Linux command line proficiency

**Interview Process:**
1. **Phone Screen (30 min):** Background & motivation
2. **Database Challenge (2 hours):** Optimize slow queries, design schema
3. **System Design (1.5 hours):** 100M event/day streaming architecture
4. **Code Review (1 hour):** Review PostgreSQL/Kafka code samples

---

#### L3 Junior Engineer (API & Infrastructure)

**Level:** L3 (Junior, 0-2 years)  
**Reports to:** Mid Backend Engineer  
**Compensation:** $130k + 0.05% equity + $20k sign-on  

**Role Summary:**
Develop FastAPI endpoints, monitoring, and deployment infrastructure. Own reliability and observability.

**Key Responsibilities:**
- Build REST API endpoints (simulations CRUD, results fetching)
- Implement Prometheus/Jaeger monitoring
- Maintain Kubernetes deployment configurations
- Write unit & integration tests (target: 90%+ coverage)
- Troubleshoot production incidents
- Document API specifications & deployment runbooks

**Requirements:**
- CS degree or equivalent (bootcamp, self-taught)
- Python proficiency (FastAPI or Flask)
- Understanding of HTTP & REST APIs
- Basic Linux & Git knowledge
- Strong communication & willingness to learn

**Interview Process:**
1. **Phone Screen (30 min):** Background & motivation
2. **Coding Challenge (1.5 hours):** Build REST API for CRUD
3. **Code Review (1 hour):** Review candidate's Python code
4. **Culture Fit (30 min):** Values, learning mindset, team dynamics

---

### AI/ML Roles

#### L5 Senior AI/ML Engineer (Agents & Narrative)

**Level:** L5 (5+ years)  
**Reports to:** VP Engineering  
**Compensation:** $200k + 0.15% equity + $30k sign-on  

**Role Summary:**
Own AI agent architecture including behavior trees, memory systems, Claude integration, and narrative generation.

**Key Responsibilities:**
- Design & implement Entity-Component System (ECS) architecture
- Build multi-layer memory systems (episodic, semantic, procedural, emotional)
- Integrate Claude API for dialogue & narrative generation
- Implement behavior trees & goal-driven motivation engine
- Design personality model (Big Five traits)
- Optimize Claude API costs & token usage

**Requirements:**
- 5+ years ML/AI engineering
- Experience with LLMs (GPT-4, Claude, or similar)
- Reinforcement learning background
- Strong Python & system design skills
- Published papers or portfolio

**Interview Process:**
1. **Phone Screen (30 min):** Background, LLM experience
2. **Take-home (6 hours):** Implement goal-driven behavior system
3. **Architecture (2 hours):** Design memory + personality system
4. **LLM Integration (1 hour):** Design cost-effective Claude integration
5. **Culture Fit (1 hour):** Collaboration, storytelling

---

### Infrastructure Roles

#### L4 DevOps/Infrastructure Engineer

**Level:** L4 (3-4 years)  
**Reports to:** VP Engineering  
**Compensation:** $160k + 0.10% equity + $25k sign-on  

**Role Summary:**
Own Kubernetes infrastructure, CI/CD pipeline, monitoring, and disaster recovery.

**Key Responsibilities:**
- Design & maintain Kubernetes HA cluster (3+ regions)
- Build CI/CD pipeline (GitHub Actions)
- Implement disaster recovery & backup automation
- Monitor cost (target: <$50k/month for 100 users)
- Implement security hardening (SOC 2 controls)
- Scale infrastructure for 10K+ concurrent users

**Requirements:**
- 3+ years DevOps/SRE experience
- Kubernetes expert (StatefulSets, Deployments, networking)
- Terraform or similar IaC
- Prometheus/Grafana monitoring
- AWS/GCP/Azure proficiency

**Interview Process:**
1. **Phone Screen (30 min):** Background, Kubernetes depth
2. **Architecture (2 hours):** Design HA multi-region cluster
3. **Troubleshooting (1 hour):** Diagnose production issues
4. **Automation (1.5 hours):** Design CI/CD pipeline

---

### Product & Design

#### P4 Senior Product Manager

**Level:** P4  
**Reports to:** CEO  
**Compensation:** $220k + 0.20% equity + $35k sign-on  

**Role Summary:**
Define product roadmap, work with customer success to prioritize features, and drive user acquisition.

**Key Responsibilities:**
- Own product strategy & quarterly roadmap
- Conduct customer interviews (target: 40+ per quarter)
- Define success metrics & track KPIs
- Work with engineering on prioritization
- Drive go-to-market for new features
- Build product analytics dashboard

**Requirements:**
- 5+ years product management
- B2B SaaS or developer tools experience
- Strong data intuition
- Customer interview skills
- Strategic thinking

**Compensation:** $220k + 0.20% equity

---

#### Design Lead (UI/UX)

**Level:** L5  
**Reports to:** Product  
**Compensation:** $180k + 0.12% equity + $30k sign-on  

**Role Summary:**
Design world generation UI, scenario builder, results dashboard. Create design system.

**Key Responsibilities:**
- Design Figma prototypes for world builder
- Build component library (buttons, forms, charts)
- Conduct user testing with customers
- Implement design in React/Next.js
- Document design system
- Guide visual & interaction design

**Requirements:**
- 5+ years product design
- Figma expert
- Basic HTML/CSS/React knowledge
- Portfolio demonstrating product thinking

---

### Sales & Operations

#### VP Sales & Marketing

**Level:** L7  
**Reports to:** CEO  
**Compensation:** $250k + 0.30% equity + $50k sign-on  

**Role Summary:**
Build sales organization, close enterprise deals, and drive go-to-market execution.

**Key Responsibilities:**
- Build sales team (2 AEs, 3 SDRs, 1 Sales Eng)
- Close 5+ enterprise pilots by month 18
- Define sales process & playbook
- Manage marketing budget & content
- Build partnerships (NVIDIA, OEMs)
- Report on sales metrics & forecasts

**Requirements:**
- 8+ years sales/marketing (3+ Enterprise SaaS)
- Experience hiring & scaling teams
- P&L responsibility
- Network in robotics/AV/gaming

---

## Part 3: Interview Framework

### Interview Rubric (Technical)

```
Scoring: 1-4 (4 = exceptional, 3 = meets expectations, 2 = below, 1 = no-hire)

1. Problem Solving (weight: 30%)
   - Breaks down complex problems
   - Explores trade-offs
   - Arrives at reasonable solution
   
2. Communication (weight: 20%)
   - Explains thinking clearly
   - Asks clarifying questions
   - Listens to feedback
   
3. Coding Ability (weight: 25%)
   - Correct implementation
   - Handles edge cases
   - Clean, readable code
   
4. Systems Thinking (weight: 15%)
   - Considers scalability
   - Thinks about tradeoffs
   - Understands constraints

5. Domain Knowledge (weight: 10%)
   - Relevant experience
   - Understands robotics/simulation (nice-to-have)
```

### Take-Home Assignment Example

**Title:** Build a Traffic Simulation System (4-6 hours)

**Prompt:**
```
Implement a traffic simulation where:
- N vehicles start at random positions
- Each vehicle has a goal destination
- Vehicles must avoid collisions
- Vehicles use A* pathfinding to reach goals
- Simulate 60 seconds of movement

Deliverables:
1. Python code (main.py)
2. Simulate 100 vehicles without crashes
3. Visualize in matplotlib or Plotly
4. Write test cases (pytest)

Scoring:
- Does it run? (20 points)
- Correct pathfinding? (20 points)
- Collision avoidance? (20 points)
- Clean code & tests? (20 points)
- Performance (100 vehicles < 1s/frame)? (20 points)

Submit: GitHub link with README
```

### Culture Fit Interview

**Questions:**
1. Tell me about your last team project. What was your role?
2. Describe a time you disagreed with a teammate. How did you resolve it?
3. What excites you about PyRoboSimulator?
4. How do you approach learning new technologies?
5. Tell me about your remote work experience.
6. What kind of feedback do you value most?

**Scoring:**
- Collaboration & teamwork
- Growth mindset & learning
- Alignment with values
- Communication clarity
- Technical passion

---

## Part 4: Onboarding Checklist

### Week 1: Foundation

**Day 1 (Monday)**
- [ ] Laptop setup (MacBook, IDE, tools)
- [ ] Accounts created (Slack, GitHub, Jira, Linear)
- [ ] Repository access (GitHub, read-only at first)
- [ ] Welcome meeting with manager (30 min)
- [ ] Team introduction (1 hour)

**Day 2-3: Orientation**
- [ ] Company handbook & values review
- [ ] Security training (30 min)
- [ ] Infrastructure overview (1 hour)
- [ ] Architecture overview (2 hours)

**Day 4-5: Coding**
- [ ] First PR: Add name to TEAM.md
- [ ] Set up local environment (dev.md guide)
- [ ] Run test suite locally
- [ ] Deploy to staging (with help)

### Week 2-3: First Project

**Week 2**
- [ ] Assigned: Small bug fix or feature
- [ ] Code review with mentor (2-3 rounds)
- [ ] Merged: First production PR
- [ ] Architecture: Pair program on design
- [ ] Meetings: Standup (daily), 1:1 (weekly)

**Week 3**
- [ ] Assigned: Medium feature (2-3 days)
- [ ] Documentation: Add to wiki
- [ ] Testing: Write unit tests
- [ ] Pairing: Continued mentorship

### Week 4: Ramping Up

- [ ] Small features independently
- [ ] Code reviews: Start reviewing others' code
- [ ] On-call rotation: Shadow on-call engineer
- [ ] Project: Own small component

### Month 2: Productive

- [ ] 2-3 features per week
- [ ] Code review lead on PRs
- [ ] Participate in architecture discussions
- [ ] Mentor incoming engineers

---

## Part 5: Career Ladder

### Engineering Ladder

```
L3: Junior Engineer
    Scope: Feature implementation
    Impact: Individual contributor
    Time: 1-2 years to L4

L4: Mid Engineer
    Scope: System or subsystem owner
    Impact: Leads projects, mentors juniors
    Time: 2-3 years to L5

L5: Senior Engineer
    Scope: Multiple systems or full project
    Impact: Technical leadership, architecture
    Time: 3-5 years to L6

L6: Staff Engineer
    Scope: Platform or infrastructure
    Impact: Cross-functional leadership
    Examples: Database performance, architecture

L7: Principal Engineer
    Scope: Company-wide technical direction
    Impact: Vision & strategy
    Reports to: CTO
```

### Promotion Criteria

**L3 → L4 (After 1-2 years)**
- ✅ Consistently ships features without supervision
- ✅ Mentors 1 junior engineer
- ✅ Leads design of 1-2 projects
- ✅ Takes ownership of subsystem (caching, monitoring)
- ✅ Demonstrates system thinking

**L4 → L5 (After 2-3 years)**
- ✅ Leads major projects (quarter-long)
- ✅ Mentors 2+ engineers
- ✅ Drives technical decisions across team
- ✅ Owns performance/reliability improvements
- ✅ Strong communication to non-technical stakeholders

**L5 → L6+ (Rare, 3-5 years)**
- ✅ Recognized technical expert (internal/external)
- ✅ Leads company-wide initiatives
- ✅ Published work or talks
- ✅ Exceptional communication & influence

---

## Hiring Timeline

### Month 4 (Series A Funding)
- Hire: 1 Senior Backend Engineer (L5)
- Hire: 1 Product Manager (P3)
- Hire: 1 Sales/Biz Dev (BD)

### Month 8-12
- Hire: 2 Mid Backend Engineers (L4)
- Hire: 1 Senior AI/ML Engineer (L5)
- Hire: 1 Product Manager (P4)
- Hire: 2 Sales/Marketing
- Hire: 1 Operations

### Month 16-22
- Hire: 2 Junior Engineers (L3)
- Hire: 1 DevOps/Infrastructure (L4)
- Hire: 1 Design Lead
- Hire: 1 Customer Success Lead
- Hire: 3 Account Executives (L4-L5 external sales)

### Year 2
- Scale to 50+ (hiring parallelized)

---

**Hiring Guides & Job Descriptions Complete**  
**Ready for Series A Scaling**
