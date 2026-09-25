"""
Pre-computed extractions for the five demo meetings.

Stored statically so the demo workspace loads instantly,
with zero LLM calls and zero API cost.

Save this file as UTF-8 (no BOM).
"""

SEED_MEETINGS = [
    {
        "file": "meeting4.txt",
        "title": "Project Nimbus – Requirements Brainstorm",
        "date": "2025-02-25",
        "participants": "Rahul Sharma, Ananya Iyer, Vikram Rao, Sneha Kulkarni",
        "summary": (
            "The team held an early requirements brainstorm before formally committing to "
            "Project Nimbus. They agreed to build a campus event booking app, decided to use "
            "cloud-hosted infrastructure, and left payment scope, budget, and domain ownership "
            "open for the kickoff meeting. A one-page project charter was assigned to Sneha."
        ),
        "key_points": [
            "Existing campus booking apps have poor UX and lack basic filtering.",
            "The MVP will focus on event list, event detail, and booking confirmation screens.",
            "Infrastructure will be cloud-hosted rather than on-premise.",
            "Whether payment is in scope for the MVP depends on the Dean's office conversation.",
            "The project charter will formalize the target launch goal of end of April.",
        ],
        "decisions": [
            "Project Nimbus will be built as a campus event booking app.",
            "Infrastructure will use cloud-hosted services — no on-premise setup.",
        ],
        "action_items": [
            {"task": "Prepare a mock-up for the booking flow", "assignee": "Ananya Iyer", "deadline": "2025-02-28", "priority": "Medium", "status": "Completed"},
            {"task": "Draft the one-page project charter", "assignee": "Sneha Kulkarni", "deadline": "2025-03-01", "priority": "Medium", "status": "Completed"},
        ],
        "risks": [
            "Choosing the wrong tech stack early could create costly rework later.",
        ],
        "unresolved_questions": [
            "Is payment in scope for the MVP, or is it free-events only?",
            "Who owns the domain name and hosting account?",
            "What is the budget ceiling for the project?",
        ],
    },
    {
        "file": "meeting1.txt",
        "title": "Project Nimbus – Kickoff & Planning",
        "date": "2025-03-04",
        "participants": "Rahul Sharma, Ananya Iyer, Vikram Rao, Sneha Kulkarni, Arjun Mehta",
        "summary": (
            "The team kicked off Project Nimbus, a campus event booking app. Razorpay was "
            "selected as the payment gateway, React Native and FastAPI with PostgreSQL were "
            "confirmed as the stack, and weekly standups were set for Wednesday at 5pm. "
            "Key risks identified were the three-week college approval process, Razorpay KYC "
            "delays, and the mid-semester exam period."
        ),
        "key_points": [
            "Project Nimbus is a campus event booking app targeting a working pilot before the end of the semester.",
            "Ananya compared Razorpay, PayU and Instamojo; Razorpay was judged to have the cleanest React Native SDK and lowest setup effort.",
            "Any app collecting money from students requires written approval from the Dean's office, which takes about three weeks.",
            "A user survey is needed before the booking flow is finalized.",
            "Mid-semester exams run from 14 to 22 March and will slow the team down.",
        ],
        "decisions": [
            "Razorpay will be used as the payment gateway.",
            "The mobile client will be built in React Native and the backend in FastAPI with PostgreSQL.",
            "Weekly standups will be held every Wednesday at 5pm.",
        ],
        "action_items": [
            {"task": "Finalize the Razorpay merchant account and complete KYC", "assignee": "Rahul Sharma", "deadline": "2025-03-10", "priority": "High", "status": "Completed"},
            {"task": "Submit the Dean's office approval application form", "assignee": "Arjun Mehta", "deadline": "2025-03-18", "priority": "High", "status": "In Progress"},
            {"task": "Prepare a user survey and collect at least 50 responses", "assignee": "Sneha Kulkarni", "deadline": "2025-03-08", "priority": "Low", "status": "Completed"},
            {"task": "Design the onboarding screens", "assignee": "Ananya Iyer", "deadline": "2025-03-12", "priority": "Medium", "status": "Completed"},
            {"task": "Set up the CI/CD pipeline and staging environment", "assignee": "Vikram Rao", "deadline": "2025-03-15", "priority": "Medium", "status": "Completed"},
        ],
        "risks": [
            "College approval from the Dean's office may take up to three weeks, which could delay the pilot.",
            "Razorpay KYC approval may be delayed by additional documentation requests.",
            "Mid-semester exams from 14 to 22 March will reduce team velocity.",
        ],
        "unresolved_questions": [
            "Should the pilot support card payments in addition to UPI?",
            "What refund policy will the app declare?",
            "Which venue will be used for the pilot event?",
        ],
    },
    {
        "file": "meeting2.txt",
        "title": "Project Nimbus – Payment Integration Progress Review",
        "date": "2025-03-11",
        "participants": "Rahul Sharma, Ananya Iyer, Vikram Rao, Arjun Mehta",
        "summary": (
            "The team reviewed payment integration progress. The Razorpay merchant account was "
            "created but KYC remained pending, so the team decided to stay in test mode. A "
            "webhook signature verification issue was identified as the main technical blocker. "
            "The team also decided to support UPI only for the pilot and to move standups to "
            "Thursday at 5pm."
        ),
        "key_points": [
            "The Razorpay merchant account is created but KYC is still pending due to an additional address proof request.",
            "Payments succeed in test mode but the webhook rejects the signature, which risks duplicate bookings.",
            "Card payments would significantly increase the compliance surface for a student project.",
            "The Wednesday 5pm standup clashes with Vikram's lab schedule.",
        ],
        "decisions": [
            "The team will stay in Razorpay test mode until KYC is approved; production keys are off limits.",
            "The pilot will support UPI only; card payments move to phase two.",
            "Weekly standups move from Wednesday 5pm to Thursday 5pm starting this week.",
        ],
        "action_items": [
            {"task": "Resolve the Razorpay webhook signature verification issue", "assignee": "Rahul Sharma", "deadline": "2025-03-14", "priority": "High", "status": "Completed"},
            {"task": "Add retry logic and idempotency keys for failed payments", "assignee": "Vikram Rao", "deadline": "2025-03-16", "priority": "Medium", "status": "Completed"},
            {"task": "Update the payment failure UI with an error message and retry button", "assignee": "Ananya Iyer", "deadline": "2025-03-15", "priority": "Medium", "status": "Completed"},
            {"task": "Submit the approval form to the Dean's office", "assignee": "Arjun Mehta", "deadline": "2025-03-13", "priority": "High", "status": "Completed"},
            {"task": "Follow up with the Dean's office in person", "assignee": "Arjun Mehta", "deadline": "2025-03-13", "priority": "High", "status": "Completed"},
        ],
        "risks": [
            "The webhook signature issue could cause duplicate bookings and undermine trust in the payment flow.",
            "Razorpay KYC is still not approved, blocking production deployment.",
            "The college approval has not come through and exam week starts on 14 March.",
        ],
        "unresolved_questions": [
            "What refund policy will the app declare?",
            "Who will own the production API keys?",
            "Do we need GST invoices for the pilot?",
        ],
    },
    {
        "file": "meeting3.txt",
        "title": "Project Nimbus – Final Project Review",
        "date": "2025-03-20",
        "participants": "Rahul Sharma, Ananya Iyer, Vikram Rao, Sneha Kulkarni, Arjun Mehta",
        "summary": (
            "The team held the final review before launch. The webhook issue was resolved and "
            "the pilot launch was set for 5 April 2025 with UPI-only payments. Sneha was "
            "assigned ownership of user support, a feature freeze was declared, and the "
            "outstanding written college approval was flagged as the biggest external risk."
        ),
        "key_points": [
            "The Dean's office has verbally approved the project but the written approval letter has not arrived.",
            "The webhook signature issue is fixed and idempotency keys are in place.",
            "Rahul is the only person who knows the production deployment process, creating a single point of failure.",
            "The pilot event venue was never decided; the team will run it online.",
        ],
        "decisions": [
            "The pilot launches on 5 April 2025.",
            "The pilot supports UPI only; card payments remain in phase two.",
            "Sneha Kulkarni owns user support for the pilot.",
            "Feature freeze is in effect from today until after the pilot.",
            "The pilot launch event will be held online.",
        ],
        "action_items": [
            {"task": "Finalize production keys and perform the final deployment", "assignee": "Rahul Sharma", "deadline": "2025-03-28", "priority": "High", "status": "In Progress"},
            {"task": "Document the deployment runbook", "assignee": "Rahul Sharma", "deadline": "2025-03-28", "priority": "Medium", "status": "Pending"},
            {"task": "Run load testing on the booking flow", "assignee": "Vikram Rao", "deadline": "2025-03-26", "priority": "Medium", "status": "Pending"},
            {"task": "Write the user support FAQ", "assignee": "Sneha Kulkarni", "deadline": "2025-03-25", "priority": "Medium", "status": "Pending"},
            {"task": "Finalize UI polish and ship the payment failure screen", "assignee": "Ananya Iyer", "deadline": "2025-03-24", "priority": "Low", "status": "Completed"},
        ],
        "risks": [
            "The written college approval letter has still not arrived, which is the biggest external risk to launch.",
            "Rahul is a single point of failure for production deployment.",
            "Load testing has not been completed yet.",
        ],
        "unresolved_questions": [
            "What will the post-launch support hours be?",
            "What is the marketing budget for the pilot?",
            "Where will the physical launch event be held after the online pilot?",
        ],
    },
    {
        "file": "meeting5.txt",
        "title": "Project Nimbus – Post-Launch Retrospective",
        "date": "2025-04-12",
        "participants": "Rahul Sharma, Ananya Iyer, Vikram Rao, Sneha Kulkarni, Arjun Mehta",
        "summary": (
            "One week after the pilot launch, the team reviewed early metrics: 218 signups, "
            "47 completed bookings, zero payment failures, and only six support tickets. The "
            "written Dean's office approval finally arrived. The team decided to keep UPI-only "
            "payments for phase two, publish a refund policy by 20 April, and defer card "
            "payments and save-for-later until later phases."
        ),
        "key_points": [
            "218 unique students signed up in week one; 47 bookings were completed.",
            "Zero payment failures were recorded and p95 latency stayed under 400ms.",
            "Support volume was low — six tickets, mostly about the refund flow.",
            "Students requested 'save for later' and calendar invite features.",
            "The written Dean's office approval has finally been issued.",
        ],
        "decisions": [
            "A written refund policy will be published by 20 April.",
            "Calendar invites go into phase two; save-for-later is postponed pending more demand.",
            "UPI-only payments remain in effect through phase two; card payments will be revisited in Q3.",
            "Future launches stay online until the user base grows.",
        ],
        "action_items": [
            {"task": "Draft and publish the written refund policy", "assignee": "Sneha Kulkarni", "deadline": "2025-04-20", "priority": "High", "status": "In Progress"},
            {"task": "Have an engineer other than Rahul run through the deployment on staging", "assignee": "Vikram Rao", "deadline": "2025-04-18", "priority": "Medium", "status": "Pending"},
            {"task": "Prepare the phase-two planning meeting agenda", "assignee": "Rahul Sharma", "deadline": "2025-04-19", "priority": "Medium", "status": "Pending"},
        ],
        "risks": [
            "The deployment runbook has only been tested by Rahul and Vikram, creating a bus-factor risk.",
            "Support hours after the pilot are undefined and could create an expectation gap.",
        ],
        "unresolved_questions": [
            "What will the post-pilot support hours be?",
            "What should happen to inactive accounts after 90 days?",
            "What is the marketing budget for phase two?",
        ],
    },
]