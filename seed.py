"""Seeds the database with demo creators, prompts, purchases, and reviews
so the marketplace looks and works like a real, populated product on first run.

All demo accounts use the password:  password123
"""
from werkzeug.security import generate_password_hash


def seed_data(db):
    pw = generate_password_hash("password123")

    creators = [
        ("Ava Chen", "ava@promptsphere.ai",
         "Marketing prompt engineer. Ex-growth lead, obsessed with conversion copy."),
        ("Marcus Reid", "marcus@promptsphere.ai",
         "Former data scientist writing prompts for coding, debugging, and analysis."),
        ("Priya Nair", "priya@promptsphere.ai",
         "Educator building AI workflows and lesson templates for teachers."),
    ]
    creator_ids = []
    for name, email, bio in creators:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, role, bio) VALUES (?, ?, ?, 'creator', ?)",
            (name, email, pw, bio),
        )
        creator_ids.append(cur.lastrowid)
    ava, marcus, priya = creator_ids

    buyer_cur = db.execute(
        "INSERT INTO users (name, email, password_hash, role, bio) VALUES (?, ?, ?, 'buyer', ?)",
        ("Demo Buyer", "buyer@promptsphere.ai", pw, "Just here to browse and buy great prompts."),
    )
    demo_buyer = buyer_cur.lastrowid

    prompts = [
        dict(
            creator_id=ava,
            title="High-Converting Product Description Generator",
            description="Turns a raw product spec sheet into persuasive, SEO-ready ecommerce copy in your brand voice — headline, bullets, and long-form description.",
            category="Marketing", target_model="GPT-4", price=12.0,
            content=(
                "You are an expert ecommerce copywriter. I will give you a product name, "
                "a list of features, and a target audience. Write:\n"
                "1. A benefit-driven headline (max 10 words)\n"
                "2. Five scannable bullet points, each leading with a benefit then the feature\n"
                "3. A 120-150 word product description in a [BRAND VOICE] tone\n"
                "4. Three SEO keywords naturally woven into the copy\n\n"
                "Product name: [PRODUCT]\nFeatures: [FEATURE LIST]\nAudience: [AUDIENCE]\nBrand voice: [BRAND VOICE]\n\n"
                "Do not invent features that weren't given. Keep claims honest and specific."
            ),
        ),
        dict(
            creator_id=ava,
            title="Social Media Caption & Hashtag Generator",
            description="Generates platform-specific captions (Instagram, LinkedIn, X) plus a tiered hashtag set for any post topic.",
            category="Marketing", target_model="Gemini", price=7.0,
            content=(
                "Act as a social media strategist. For the topic and platform I give you, produce:\n"
                "- 3 caption variants (short punchy / storytelling / question-based)\n"
                "- A tiered hashtag list: 3 broad, 4 niche, 3 micro-niche\n"
                "- One suggested call-to-action line\n\n"
                "Topic: [TOPIC]\nPlatform: [PLATFORM]\nTone: [TONE]\n\n"
                "Match each caption's length and style conventions to the platform specified."
            ),
        ),
        dict(
            creator_id=marcus,
            title="Code Review & Refactor Assistant",
            description="Reviews a code snippet for bugs, security issues, and readability, then returns a refactored version with inline explanations.",
            category="Coding & Development", target_model="Claude", price=15.0,
            content=(
                "You are a senior software engineer performing a code review. Given the code block and "
                "language below:\n"
                "1. List any bugs or edge cases you find, with severity (low/medium/high)\n"
                "2. Flag any security concerns\n"
                "3. Suggest readability/naming improvements\n"
                "4. Provide a refactored version of the code with inline comments explaining each change\n\n"
                "Language: [LANGUAGE]\nCode:\n```\n[CODE]\n```\n\n"
                "Do not change the function's external behavior unless a bug requires it — call that out explicitly."
            ),
        ),
        dict(
            creator_id=marcus,
            title="Bug-to-Fix Diagnostic Assistant",
            description="Give it an error message and surrounding code; it walks through root-cause diagnosis before proposing a fix.",
            category="Coding & Development", target_model="GPT-5", price=16.0,
            content=(
                "You are debugging alongside me. I will provide an error message/stack trace and the "
                "relevant code. Follow this process:\n"
                "1. Restate what the error means in plain language\n"
                "2. List the 2-3 most likely root causes, ranked by probability\n"
                "3. Ask for any missing context needed to confirm the cause (if applicable)\n"
                "4. Propose a minimal fix, then a more robust long-term fix if different\n\n"
                "Error:\n[ERROR MESSAGE]\n\nCode:\n```\n[CODE]\n```\n\n"
                "Never guess silently — if you're not sure, say so and ask."
            ),
        ),
        dict(
            creator_id=marcus,
            title="CSV Insight Summarizer",
            description="Feed it a data sample and column descriptions; it returns key trends, outliers, and three suggested follow-up analyses.",
            category="Data Analysis", target_model="Claude", price=14.0,
            content=(
                "You are a data analyst. I'll give you a sample of rows from a CSV and a description of "
                "each column. Based on this:\n"
                "1. Summarize the shape and quality of the data (missing values, obvious outliers)\n"
                "2. Identify the 3 most notable trends or patterns visible in the sample\n"
                "3. Flag anything that looks like a data quality issue\n"
                "4. Suggest 3 follow-up analyses or visualizations worth running on the full dataset\n\n"
                "Column descriptions: [COLUMN DESCRIPTIONS]\nSample rows:\n[CSV SAMPLE]\n\n"
                "Be explicit about what you can and can't conclude from a small sample."
            ),
        ),
        dict(
            creator_id=priya,
            title="Lesson Plan Generator for Teachers",
            description="Creates a full standards-aligned lesson plan — objectives, warm-up, activities, and assessment — from a topic and grade level.",
            category="Education", target_model="GPT-4", price=10.0,
            content=(
                "You are an experienced curriculum designer. Build a complete lesson plan for:\n"
                "Grade level: [GRADE]\nSubject/topic: [TOPIC]\nDuration: [MINUTES] minutes\n"
                "Learning standard (if any): [STANDARD]\n\n"
                "Include:\n"
                "1. 2-3 measurable learning objectives\n"
                "2. A 5-minute warm-up/hook activity\n"
                "3. Main activity with step-by-step instructor directions\n"
                "4. A quick formative assessment question or exit ticket\n"
                "5. One differentiation suggestion for struggling students and one for advanced students"
            ),
        ),
        dict(
            creator_id=priya,
            title="Study Guide & Flashcard Builder",
            description="Turns any textbook chapter or notes into a condensed study guide plus ready-to-use Q&A flashcards.",
            category="Education", target_model="Any Model", price=6.0,
            content=(
                "Act as a study coach. Given the notes or chapter text below, produce:\n"
                "1. A one-page summary organized under clear subheadings\n"
                "2. 10 flashcard-style Q&A pairs covering the most testable facts and concepts\n"
                "3. Three likely exam-style questions with model answers\n\n"
                "Source material:\n[NOTES OR CHAPTER TEXT]\n\n"
                "Keep the summary at a level appropriate for [GRADE/LEVEL]."
            ),
        ),
        dict(
            creator_id=priya,
            title="Daily Priority & Time-Blocking Planner",
            description="Takes a messy to-do list and turns it into a prioritized, time-blocked daily schedule.",
            category="Productivity", target_model="Any Model", price=6.0,
            content=(
                "You are a productivity coach. I will give you today's task list and my working hours. "
                "Return:\n"
                "1. Tasks grouped into Urgent/Important quadrants\n"
                "2. A realistic time-blocked schedule for the day, including a lunch break\n"
                "3. One task you'd recommend cutting or delegating, with reasoning\n\n"
                "Working hours: [START] to [END]\nTasks: [TASK LIST]\n\n"
                "Assume each task's rough duration if not given, and say which durations you assumed."
            ),
        ),
        dict(
            creator_id=ava,
            title="SWOT & Competitive Analysis Builder",
            description="Generates a structured SWOT and side-by-side competitor comparison from basic company and market info.",
            category="Business & Strategy", target_model="Claude", price=18.0,
            content=(
                "You are a strategy consultant. Using the company and competitor info below, produce:\n"
                "1. A four-quadrant SWOT analysis (2-3 points per quadrant)\n"
                "2. A comparison table of the company vs. up to 3 competitors across: pricing, "
                "target customer, key differentiator, and biggest weakness\n"
                "3. Two strategic recommendations based on the analysis\n\n"
                "Company: [COMPANY NAME + ONE-LINE DESCRIPTION]\nCompetitors: [COMPETITOR LIST]\n"
                "Known strengths: [STRENGTHS]\nKnown challenges: [CHALLENGES]\n\n"
                "Flag clearly any point where you are inferring rather than working from given facts."
            ),
        ),
        dict(
            creator_id=marcus,
            title="Cinematic Portrait Prompt Pack",
            description="A tested set of 10 Midjourney prompt formulas for dramatic, editorial-style portrait lighting and composition.",
            category="Image Generation", target_model="Midjourney", price=8.0,
            content=(
                "Base formula:\n"
                "[SUBJECT], cinematic portrait, dramatic [LIGHT DIRECTION] lighting, shallow depth of field, "
                "shot on [LENS/CAMERA REFERENCE], [MOOD] atmosphere, film grain, color grade "
                "reminiscent of [FILM/DIRECTOR REFERENCE] --ar 2:3 --v 6\n\n"
                "Variations included in this pack:\n"
                "- Rembrandt lighting editorial headshot\n"
                "- Rim-lit silhouette against fog\n"
                "- Golden hour backlit close-up\n"
                "- Moody single-source studio light\n"
                "- High-contrast black and white noir portrait\n"
                "(plus 5 more formulas with swap-in variables for subject, mood, and reference style)"
            ),
        ),
    ]

    prompt_ids = []
    for p in prompts:
        cur = db.execute(
            """
            INSERT INTO prompts (creator_id, title, description, category, target_model, price, content, preview, sales_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                p["creator_id"], p["title"], p["description"], p["category"],
                p["target_model"], p["price"], p["content"],
                (p["content"][:160] + "…") if len(p["content"]) > 160 else p["content"], # type: ignore
                0,
            ),
        )
        prompt_ids.append(cur.lastrowid)

    # give the demo buyer a few purchases + reviews so the UI has real content to show
    sample_purchases = [
        (demo_buyer, prompt_ids[0], 5, "Saved me hours of copywriting — output needed almost no editing."),
        (demo_buyer, prompt_ids[2], 4, "Solid review quality, though I had to nudge it for more security detail."),
        (demo_buyer, prompt_ids[5], 5, "Used this for my 6th grade class — objectives were spot on."),
        (demo_buyer, prompt_ids[8], 4, "Genuinely useful competitor table, saved me a full afternoon."),
    ]
    for buyer_id, prompt_id, rating, comment in sample_purchases:
        price = next(p["price"] for p, pid in zip(prompts, prompt_ids) if pid == prompt_id)
        db.execute(
            "INSERT INTO purchases (buyer_id, prompt_id, price_paid) VALUES (?, ?, ?)",
            (buyer_id, prompt_id, price),
        )
        db.execute("UPDATE prompts SET sales_count = sales_count + 1 WHERE id = ?", (prompt_id,))
        db.execute(
            "INSERT INTO reviews (prompt_id, buyer_id, rating, comment) VALUES (?, ?, ?, ?)",
            (prompt_id, buyer_id, rating, comment),
        )

    # bump sales_count on a few more prompts so "popular" sorting has variety, without fake purchases/reviews
    for extra_id in [prompt_ids[1], prompt_ids[6], prompt_ids[9]]:
        db.execute(
            "UPDATE prompts SET sales_count = sales_count + ? WHERE id = ?",
            (3, extra_id),
        )

    db.commit()
