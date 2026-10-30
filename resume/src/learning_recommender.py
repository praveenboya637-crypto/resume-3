"""
ResumeRank AI - Skill Gap Recommender & Learning Roadmap Engine.
Generates actionable learning roadmaps, core concepts to study, project recommendations,
and industry resources for detected skill deficits.
"""

from typing import Dict, Any, List

# Curated skill learning curriculum database
SKILL_CURRICULUM = {
    "kubernetes": {
        "title": "Kubernetes & Cloud-Native Container Orchestration",
        "key_concepts": ["Pods, Deployments, ReplicaSets", "Services, Ingress & Cluster Networking", "ConfigMaps, Secrets, Volumes", "Helm Charts & GitOps"],
        "project_idea": "Deploy a multi-tier microservice with automated rolling updates, horizontal pod autoscaling, and an Ingress controller on Minikube.",
        "recommended_resource": "Kubernetes.io Official Docs & 'Certified Kubernetes Administrator (CKA)' on Linux Foundation",
        "estimated_time": "3 - 5 weeks"
    },
    "docker": {
        "title": "Docker & Container Architecture",
        "key_concepts": ["Multi-stage Dockerfiles", "Image Layer Optimization & Caching", "Docker Compose Orchestration", "Security & Non-root Users"],
        "project_idea": "Containerize a full-stack Python/React app with a production-ready, minimal Alpine image and health checks.",
        "recommended_resource": "Docker Deep Dive (Nigel Poulton) & freeCodeCamp Docker Course",
        "estimated_time": "1 - 2 weeks"
    },
    "pytorch": {
        "title": "PyTorch Deep Learning & Neural Architectures",
        "key_concepts": ["Tensors, Autograd & Computational Graphs", "Custom Dataset & DataLoader pipelines", "Transfer Learning with Torchvision/HuggingFace", "Distributed Training with DDP"],
        "project_idea": "Build and fine-tune a vision transformer or ResNet model on a custom image classification dataset with mixed precision.",
        "recommended_resource": "Deep Learning with PyTorch (official) & Fast.ai Course",
        "estimated_time": "4 - 6 weeks"
    },
    "tensorflow": {
        "title": "TensorFlow 2.x & Keras Production Pipelines",
        "key_concepts": ["Keras Functional API", "tf.data high-performance pipelines", "TensorBoard profiling", "TF Serving & TFLite deployment"],
        "project_idea": "Build an end-to-end sentiment classification pipeline and export it as an optimized SavedModel for real-time inference.",
        "recommended_resource": "DeepLearning.AI TensorFlow Developer Professional Certificate",
        "estimated_time": "3 - 5 weeks"
    },
    "fastapi": {
        "title": "FastAPI Asynchronous Microservice Development",
        "key_concepts": ["Async/Await concurrency in Python", "Pydantic v2 data validation & serialization", "Dependency Injection system", "OpenAPI docs & OAuth2 security"],
        "project_idea": "Develop a high-throughput async REST API that processes batch ML inference with background worker tasks.",
        "recommended_resource": "FastAPI Official Documentation (Tiangolo)",
        "estimated_time": "1 - 2 weeks"
    },
    "aws": {
        "title": "Amazon Web Services (AWS) Cloud Engineering",
        "key_concepts": ["IAM Roles & Least-Privilege Policies", "EC2, ECS, and Serverless Lambda", "S3 Storage Classes & CloudFront", "VPC Subnets, Security Groups & NAT"],
        "project_idea": "Architect a serverless document ingestion pipeline using AWS Lambda, S3, API Gateway, and DynamoDB.",
        "recommended_resource": "AWS Certified Solutions Architect Associate (Stephane Maarek)",
        "estimated_time": "4 - 6 weeks"
    },
    "gcp": {
        "title": "Google Cloud Platform (GCP) Data & ML Engineering",
        "key_concepts": ["Cloud Run containerized services", "BigQuery SQL analytics & partitioning", "Vertex AI ML pipelines", "GCS & Cloud IAM"],
        "project_idea": "Deploy an auto-scaling ML inference API to Google Cloud Run connected to BigQuery for event logging.",
        "recommended_resource": "Google Cloud Skills Boost & GCP Associate Cloud Engineer",
        "estimated_time": "3 - 5 weeks"
    },
    "postgresql": {
        "title": "Advanced PostgreSQL & Relational Modeling",
        "key_concepts": ["Indexing strategies (B-tree, GIN, BRIN)", "EXPLAIN ANALYZE query optimization", "ACID transactions & MVCC locks", "Partitioning & CTEs"],
        "project_idea": "Optimize a slow million-row analytical query using composite indexes and materialized views.",
        "recommended_resource": "Use The Index, Luke! & High Performance PostgreSQL",
        "estimated_time": "2 - 3 weeks"
    },
    "react": {
        "title": "Modern React & Component State Architecture",
        "key_concepts": ["Hooks (useEffect, useMemo, useCallback)", "Custom Hooks & Composition", "State management (Zustand, Redux Toolkit)", "Server Components & Next.js"],
        "project_idea": "Build an interactive data analytics dashboard with responsive charts, dark mode, and optimistic UI updates.",
        "recommended_resource": "React.dev Official Interactive Tutorials",
        "estimated_time": "2 - 4 weeks"
    },
    "ci/cd": {
        "title": "CI/CD Automation & DevOps Pipelines",
        "key_concepts": ["GitHub Actions workflows & matrix builds", "Automated unit & lint testing suites", "Artifact caching & secrets management", "Automated deployment stages"],
        "project_idea": "Construct a GitHub Actions pipeline that triggers tests, builds a Docker image, and deploys automatically on main push.",
        "recommended_resource": "GitHub Actions Documentation & DevOps Roadmap on roadmap.sh",
        "estimated_time": "1 - 2 weeks"
    },
    "transformers": {
        "title": "Hugging Face Transformers & Modern NLP",
        "key_concepts": ["Self-Attention mechanisms & Transformer blocks", "Tokenization & vocabulary alignment", "LoRA & PEFT Parameter-Efficient Fine-Tuning", "Hugging Face pipeline inference"],
        "project_idea": "Fine-tune a lightweight LLM using LoRA on domain-specific support tickets for automated classification.",
        "recommended_resource": "Hugging Face NLP Course (Free & Interactive)",
        "estimated_time": "3 - 4 weeks"
    },
    "rag": {
        "title": "Retrieval Augmented Generation (RAG) Architecture",
        "key_concepts": ["Document chunking & embedding strategies", "Vector databases (Chroma, Pinecone, FAISS)", "Hybrid search (BM25 + Dense Vectors)", "Context re-ranking & hallucination guards"],
        "project_idea": "Create an enterprise knowledge assistant that ingests company PDF manuals and answers queries with verified citations.",
        "recommended_resource": "DeepLearning.AI LangChain & RAG Short Courses",
        "estimated_time": "2 - 3 weeks"
    }
}


def get_recommendations_for_missing_skills(missing_skills: List[str]) -> List[Dict[str, Any]]:
    """
    Returns curated learning roadmaps and suggestions for each missing skill.
    Falls back to a generalized technical upskilling curriculum if skill is not in pre-defined set.
    """
    recommendations = []
    for skill in missing_skills:
        key = skill.lower().strip()
        if key in SKILL_CURRICULUM:
            item = dict(SKILL_CURRICULUM[key])
            item["skill_name"] = skill
            recommendations.append(item)
        else:
            # Generic technical upskilling recommendation
            recommendations.append({
                "skill_name": skill,
                "title": f"Mastering {skill} Fundamentals & Best Practices",
                "key_concepts": [
                    f"Core syntax and operational principles of {skill}",
                    f"Integration patterns and standard libraries for {skill}",
                    "Testing, debugging, and production security standards",
                    "Architectural patterns in enterprise production environments"
                ],
                "project_idea": f"Implement a real-world portfolio project demonstrating hands-on proficiency in {skill} with automated tests.",
                "recommended_resource": f"Official documentation, GitHub open-source repositories, and interactive tutorials for {skill}",
                "estimated_time": "2 - 4 weeks"
            })
    return recommendations
