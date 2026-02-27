"""
scripts/refresh_portfolio.py
──────────────────────────────
Rebuild all indexes after updating portfolio.json or resume.pdf.
Optionally uploads to S3 and triggers ECS rolling deployment.

Usage:
    python scripts/refresh_portfolio.py              # local only
    python scripts/refresh_portfolio.py --deploy     # + S3 upload + ECS deploy
"""

import sys
import os
import argparse
import logging
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.ingestion.portfolio_loader import PortfolioLoader
from app.ingestion.resume_loader import ResumeLoader
from app.vectorstore.index_manager import IndexManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


def rebuild_indexes():
    logger.info("Rebuilding portfolio index...")
    portfolio_loader = PortfolioLoader()
    portfolio = portfolio_loader.load(settings.PORTFOLIO_JSON_PATH)
    portfolio_chunks = portfolio_loader.build_chunks(portfolio)

    logger.info("Rebuilding resume index...")
    resume_loader = ResumeLoader()
    resume_chunks = resume_loader.load_and_chunk(settings.RESUME_PDF_PATH)

    logger.info("Clearing GitHub repo cache...")
    github_cache = os.path.join(settings.INDEXES_DIR, "github_cache")
    if os.path.exists(github_cache):
        shutil.rmtree(github_cache)
        os.makedirs(github_cache)

    index_manager = IndexManager()
    index_manager.build_portfolio_index(portfolio_chunks)
    index_manager.build_resume_index(resume_chunks)

    logger.info(f"Done. Portfolio: {index_manager.portfolio_index.size} vecs, Resume: {index_manager.resume_index.size} vecs")
    return index_manager


def upload_to_s3():
    try:
        import boto3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        files = [
            "indexes/portfolio/index.faiss",
            "indexes/portfolio/metadata.pkl",
            "indexes/resume/index.faiss",
            "indexes/resume/metadata.pkl",
        ]
        for f in files:
            if os.path.exists(f):
                key = f
                s3.upload_file(f, settings.S3_BUCKET_NAME, key)
                logger.info(f"Uploaded {f} to s3://{settings.S3_BUCKET_NAME}/{key}")
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")


def trigger_ecs_deploy():
    try:
        import boto3
        ecs = boto3.client("ecs", region_name=settings.AWS_REGION)
        ecs.update_service(
            cluster="venkatgpt-cluster",
            service="venkatgpt-service",
            forceNewDeployment=True,
        )
        logger.info("ECS rolling deployment triggered.")
    except Exception as e:
        logger.error(f"ECS deploy failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true", help="Upload to S3 and trigger ECS deploy")
    args = parser.parse_args()

    rebuild_indexes()

    if args.deploy:
        logger.info("Uploading indexes to S3...")
        upload_to_s3()
        logger.info("Triggering ECS deployment...")
        trigger_ecs_deploy()

    logger.info("Refresh complete.")
