"""
AI Resume Screening and Job Matching System
Constants, skill dictionaries, sample job descriptions, and configuration.
"""

# Pretrained local sentence-transformers model (fast, lightweight, runs 100% locally)
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

# Default scoring weights (customizable by recruiter in the UI)
DEFAULT_SEMANTIC_WEIGHT = 0.60  # 60% weight on contextual semantic similarity
DEFAULT_SKILL_WEIGHT = 0.40     # 40% weight on exact & matched technical skills
DEFAULT_SHORTLIST_THRESHOLD = 70.0  # Percentage threshold to tag candidate as "Shortlisted"

# Ethical AI & Fair Hiring Disclaimer
ETHICAL_DISCLAIMER = (
    "⚖️ Ethical AI Notice: This system uses NLP semantic similarity and skill matching solely as a "
    "decision-support estimate. It does NOT evaluate or store protected personal characteristics "
    "(such as age, gender, race, religion, nationality, or disability status). Match scores reflect "
    "textual alignment with the submitted job description, not guaranteed candidate competency or "
    "hiring probability. Human recruiter review remains essential."
)

# Comprehensive Skill Taxonomy across modern software, AI, cloud, and engineering domains
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "c++", "c#", "c", "javascript", "typescript", "golang", "go",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "bash", "shell",
        "powershell", "perl", "dart", "html", "html5", "css", "css3"
    ],
    "AI & Machine Learning": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn",
        "hugging face", "transformers", "llm", "large language models", "generative ai",
        "genai", "rag", "retrieval augmented generation", "langchain", "llamaindex",
        "opencv", "bert", "gpt", "fine-tuning", "prompt engineering", "reinforcement learning",
        "xgboost", "lightgbm", "random forest", "neural networks", "diffusion models"
    ],
    "Data Science & Analytics": [
        "pandas", "numpy", "scipy", "data analysis", "data visualization", "matplotlib",
        "seaborn", "plotly", "tableau", "power bi", "powerbi", "excel", "statistics",
        "hypothesis testing", "a/b testing", "feature engineering", "data cleaning",
        "etl", "data pipelines", "bigquery", "dbt"
    ],
    "Web Frameworks & Backend": [
        "react", "react.js", "next.js", "angular", "vue", "vue.js", "node.js", "nodejs",
        "express", "express.js", "django", "flask", "fastapi", "spring boot", "springboot",
        "asp.net", ".net", "laravel", "ruby on rails", "graphql", "rest api", "restful api",
        "microservices", "websockets", "tailwind css", "bootstrap"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "gcp", "google cloud", "docker",
        "kubernetes", "k8s", "ci/cd", "jenkins", "github actions", "gitlab ci",
        "terraform", "ansible", "helm", "linux", "nginx", "apache", "prometheus",
        "grafana", "cloudformation", "serverless", "lambda"
    ],
    "Databases & Big Data": [
        "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "oracle",
        "cassandra", "dynamodb", "elasticsearch", "neo4j", "snowflake", "databricks",
        "apache spark", "spark", "kafka", "hadoop", "hive"
    ],
    "Engineering Practices & Tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "agile", "scrum", "kanban",
        "unit testing", "pytest", "junit", "tdd", "test driven development",
        "code review", "system design", "object oriented programming", "oop",
        "design patterns", "ci/cd pipeline", "debugging"
    ],
    "Soft Skills & Management": [
        "problem solving", "critical thinking", "communication", "team collaboration",
        "leadership", "mentoring", "project management", "time management",
        "adaptability", "cross-functional collaboration", "stakeholder management"
    ]
}

# Flattened lookup mapping: lowercase skill -> display name & category
ALL_SKILLS_LOOKUP = {}
for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        ALL_SKILLS_LOOKUP[skill.lower()] = {
            "display": skill.title() if len(skill) > 4 else skill.upper(),
            "category": category
        }
# Custom display exceptions for common capitalized acronyms and proper names
SPECIAL_DISPLAYS = {
    "c++": "C++",
    "c#": "C#",
    "sql": "SQL",
    "nlp": "NLP",
    "llm": "LLM",
    "aws": "AWS",
    "gcp": "GCP",
    "k8s": "K8s",
    "ci/cd": "CI/CD",
    "rest api": "REST API",
    "restful api": "RESTful API",
    "ui/ux": "UI/UX",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "fastapi": "FastAPI",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "github actions": "GitHub Actions",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "next.js": "Next.js",
    "vue.js": "Vue.js",
    "react.js": "React",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "java": "Java",
    "git": "Git",
    "rust": "Rust",
    "ruby": "Ruby",
    "bash": "Bash",
    "perl": "Perl",
    "dart": "Dart",
    "jira": "Jira",
    "scrum": "Scrum",
    "agile": "Agile",
    "linux": "Linux",
    "nginx": "Nginx"
}
for k, v in SPECIAL_DISPLAYS.items():
    if k in ALL_SKILLS_LOOKUP:
        ALL_SKILLS_LOOKUP[k]["display"] = v
    else:
        ALL_SKILLS_LOOKUP[k] = {"display": v, "category": "Tech"}

# Canonical Synonym & Variation Mapping (resolves abbreviations and alternate phrasings)
SKILL_SYNONYMS = {
    # AI & ML
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "llm": "large language models",
    "llms": "large language models",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "generative artificial intelligence": "generative ai",
    "rag": "retrieval augmented generation",
    "retrieval-augmented generation": "retrieval augmented generation",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tf": "tensorflow",
    "hf": "hugging face",
    "huggingface": "hugging face",
    
    # Cloud & DevOps
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "microsoft azure": "azure",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "ci/cd pipeline": "ci/cd",
    "continuous integration": "ci/cd",
    "github-actions": "github actions",
    "gh actions": "github actions",
    "gitlab": "gitlab ci",
    
    # Programming & Web
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "nextjs": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "springboot": "spring boot",
    "fast-api": "fastapi",
    "tailwind": "tailwind css",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    
    # Databases & Big Data
    "postgres": "postgresql",
    "mongo": "mongodb",
    "spark": "apache spark",
    
    # Analytics & BI
    "powerbi": "power bi",
    "power-bi": "power bi",
    
    # Practices & Methodologies
    "tdd": "test driven development",
    "oop": "object oriented programming",
    "oops": "object oriented programming",
    "unit test": "unit testing",
    "automated testing": "unit testing"
}


# Sample Job Descriptions for instantaneous 1-click evaluation
SAMPLE_JOB_DESCRIPTIONS = {
    "AI / Machine Learning Engineer": """Job Title: AI / Machine Learning Engineer
Department: Artificial Intelligence & Data Innovations
Location: Hybrid / Remote

About the Role:
We are seeking an innovative AI / Machine Learning Engineer to design, build, and deploy production-grade machine learning models and Generative AI applications. You will collaborate with data scientists and software engineers to translate business requirements into state-of-the-art NLP, Deep Learning, and predictive systems.

Key Responsibilities:
- Design, train, evaluate, and deploy Machine Learning and Deep Learning models using Python, PyTorch, and Scikit-Learn.
- Build NLP pipelines, embeddings, and Retrieval Augmented Generation (RAG) architectures with Hugging Face Transformers and LangChain.
- Containerize models using Docker and deploy scalable inference microservices on AWS or Azure using FastAPI and Kubernetes.
- Implement CI/CD pipelines for automated testing, model tracking, and continuous integration via GitHub Actions.
- Optimize model latency, throughput, and memory footprint in production environments.
- Collaborate in an Agile/Scrum team, conducting code reviews and maintaining clean, well-documented codebases.

Required Qualifications & Skills:
- Proficiency in Python, SQL, and data science libraries including Pandas, NumPy, and Scikit-Learn.
- Strong hands-on experience with PyTorch or TensorFlow for Deep Learning and Natural Language Processing (NLP).
- Experience with Transformers, Hugging Face, LLM prompt engineering, or vector databases.
- Familiarity with Docker, FastAPI, Git, and REST APIs for machine learning deployment.
- Understanding of software engineering principles, Unit Testing (pytest), and cloud computing (AWS/GCP).
- Strong problem solving, analytical thinking, and cross-functional team collaboration skills.
""",

    "Full-Stack Web Developer (Python + React)": """Job Title: Full-Stack Web Developer (Python & React)
Department: Web & Cloud Products
Location: Bengaluru, India / Remote

About the Role:
We are looking for a skilled Full-Stack Developer to build responsive, scalable, and high-performance web applications. You will be responsible for end-to-end development, from designing dynamic React frontend components to developing robust backend REST APIs and microservices in Python.

Key Responsibilities:
- Develop modern, responsive user interfaces using React, TypeScript, HTML5, and Tailwind CSS.
- Design, build, and maintain high-performance backend microservices using Python (FastAPI or Django) and Node.js.
- Architect and query relational and NoSQL databases, including PostgreSQL, MySQL, and Redis.
- Build secure, scalable RESTful APIs and WebSocket interfaces with authentication and caching.
- Package applications using Docker containers and participate in CI/CD pipeline automation via GitHub Actions.
- Write robust unit tests, participate in sprint planning, and conduct peer code reviews.

Required Qualifications & Skills:
- Strong programming experience in Python, JavaScript, and TypeScript.
- Demonstrated hands-on expertise with React, Next.js, and modern CSS frameworks.
- Backend proficiency with FastAPI, Django, Flask, or Node.js.
- Strong knowledge of PostgreSQL, MongoDB, Redis, and SQL query optimization.
- Familiarity with Docker, Git version control, REST APIs, and Linux server environments.
- Excellent communication skills, agile teamwork, and dedication to code quality.
""",

    "Data Scientist & Analytics Specialist": """Job Title: Data Scientist & Analytics Specialist
Department: Enterprise Analytics & Business Intelligence
Location: Remote / Hybrid

About the Role:
We are looking for a Data Scientist to transform large-scale raw data into actionable business intelligence and predictive models. You will work closely with product managers and executives to define metrics, build statistical algorithms, and communicate data-driven insights through interactive dashboards.

Key Responsibilities:
- Perform exploratory data analysis (EDA), statistical modeling, and hypothesis testing on large customer datasets.
- Develop predictive machine learning models using Python, Pandas, NumPy, and Scikit-Learn.
- Build and maintain automated ETL data pipelines and query structured data from PostgreSQL and Snowflake.
- Design interactive data visualizations and executive dashboards using Tableau, Power BI, and Plotly.
- Conduct A/B testing and design experiments to evaluate product features and user engagement.
- Present analytical findings and strategic recommendations to non-technical stakeholders.

Required Qualifications & Skills:
- Bachelor's or Master's degree in Computer Science, Statistics, Mathematics, or related field.
- Advanced proficiency in Python, SQL, Pandas, NumPy, and Scikit-Learn.
- Experience with data visualization tools (Tableau, Power BI, Matplotlib, Seaborn).
- Practical knowledge of Machine Learning algorithms (Random Forest, XGBoost, Regression, Clustering).
- Familiarity with BigQuery, Snowflake, or Apache Spark is a plus.
- Strong critical thinking, storytelling with data, and communication skills.
""",

    "Cloud & DevOps Engineer": """Job Title: Cloud & DevOps Engineer
Department: Platform Engineering & Infrastructure
Location: Full-Time / Remote

About the Role:
We are hiring a Cloud & DevOps Engineer to design, automate, and maintain resilient cloud infrastructure and deployment pipelines. You will lead cloud security, container orchestration, monitoring, and automated provisioning to guarantee high availability and rapid software release cycles.

Key Responsibilities:
- Design and administer cloud environments on AWS or Azure using Infrastructure as Code (Terraform).
- Containerize microservice applications using Docker and manage orchestration using Kubernetes (K8s).
- Build, optimize, and maintain automated CI/CD pipelines using GitHub Actions, Jenkins, or GitLab CI.
- Implement comprehensive observability, logging, and monitoring using Prometheus, Grafana, and ELK.
- Ensure cloud infrastructure security, identity access management (IAM), and compliance.
- Automate configuration and deployment tasks using Bash, Shell, and Python scripting.

Required Qualifications & Skills:
- Hands-on expertise with AWS or Azure cloud architectures and IAM policies.
- Strong containerization and orchestration knowledge with Docker and Kubernetes.
- Experience with Infrastructure as Code using Terraform or Ansible.
- Proficiency in CI/CD automation with GitHub Actions or Jenkins.
- Scripting fluency in Linux, Bash, and Python.
- Knowledge of Nginx, networking protocols, SSL/TLS, and monitoring tools like Prometheus and Grafana.
"""
}
