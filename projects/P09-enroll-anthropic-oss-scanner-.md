# P09 — Enroll in Anthropic OSS Scanner

Add SECURITY.md, scanner Dockerfile, and threat model; open the enrollment PR

### Open questions
- Will a 24-star template repo pass the scanner's eligibility review?

### Notes
T01 SECURITY.md revised — done (364478b).
T02 .oss-scanner/Dockerfile: COPY . /src, all deps installed at build; tests must pass under docker run --network none.
T03 .oss-scanner/threat_model.md: web service + CLI input; init scaffolding, prototypes/, research/, docs out of scope.
T04 Enrollment PR to anthropics/oss-scanner: projects/py-launch-blueprint/project.yaml, primary_contact steve.morin@gmail.com, run tools/validate.py.

<!-- Idea state. Minimal by convention.
     Promote with `project-refine P09` when ready. -->
