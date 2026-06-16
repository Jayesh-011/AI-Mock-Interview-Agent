# ============================================================
#     RAG Based Question Scraper
# ============================================================
# Author       : Jayesh Patil
# Date         : 16/06/2026
#
# Description  : Background service that fetches interview questions 
#                from the internet and stores them in MongoDB in a 
#                normalized format.
# ============================================================

import asyncio
import json
import logging
import re
from datetime import datetime, timezone

import ollama
import trafilatura
from ddgs import DDGS
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError


MODEL = "qwen2.5:3b"
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "Interview_Questions"
COLLECTION_NAME = "questions"
FETCH_INTERVAL_SECONDS = 10


TOPIC_QUERIES = [
    "Python interview questions",
    "OOP interview questions",
    "Machine Learning interview questions",
    "Deep Learning interview questions",
    "Transformer interview questions",
    "LLM interview questions",
    "RAG interview questions",
    "AI Agent interview questions",
]


def debug_print(function_name: str, output):
    """
    Function Name : debug_print
    Description   : Prints the function name and a readable preview of its output.
    Parameters    :
        function_name : Name of the function whose output is being printed
        output        : Output value to print
    """
    print(f"\n{'=' * 80}")
    print(f"Function : {function_name}")
    print("Output   :")

    if isinstance(output, str):
        preview = output[:1200]
        print(preview if preview else "Empty string")
        if len(output) > 1200:
            print("... [truncated]")
    else:
        print(output)

    print(f"{'=' * 80}\n")


class InterviewQuestionIngestor:
    """
    Class Name     : InterviewQuestionIngestor
    Description    : Background service that fetches interview questions from the internet
                     and stores them in MongoDB in normalized format.
    """

    def __init__(self, mongo_uri: str, database_name: str, collection_name: str, model: str):
        """
        Function Name : __init__
        Description   : Initializes database connection, collection handle, and model settings.
        Parameters    :
            mongo_uri        : MongoDB connection URI
            database_name    : Name of the MongoDB database
            collection_name  : Name of the MongoDB collection
            model            : Ollama model name used for question extraction
        """
        self.mongo_client = MongoClient(mongo_uri)
        self.database = self.mongo_client[database_name]
        self.collection = self.database[collection_name]
        self.model = model
        self._ensure_indexes()
        debug_print("__init__", f"Connected to DB={database_name}, Collection={collection_name}, Model={model}")

    def _ensure_indexes(self):
        """
        Function Name : _ensure_indexes
        Description   : Creates required MongoDB indexes to prevent duplicate questions
                        and support efficient querying.
        Parameters    :
            None
        """
        self.collection.create_index("question", unique=True)
        self.collection.create_index("topic")
        self.collection.create_index("source_url")
        debug_print("_ensure_indexes", "Indexes created: question(unique), topic, source_url")

    def search_urls(self, query: str, max_results: int = 5) -> list[str]:
        """
        Function Name : search_urls
        Description   : Searches the web using DDGS and returns candidate result URLs.
        Parameters    :
            query       : Search query string
            max_results : Maximum number of URLs to collect
        """
        url_links = []

        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)

                for result in results:
                    href = result.get("href")
                    title = result.get("title", "")

                    if href and href.startswith("http"):
                        print(f"Title : {title}")
                        print(f"URL   : {href}")
                        url_links.append(href)

        except Exception as error:
            debug_print("search_urls.error", str(error))
            return []

        debug_print("search_urls", url_links)
        return url_links

    async def fetch_page_text(self, url: str) -> str:
        """
        Function Name : fetch_page_text
        Description   : Downloads a web page using Trafilatura and extracts readable text.
        Parameters    :
            url : URL of the web page
        """
        try:
            downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)

            if not downloaded:
                debug_print("fetch_page_text", f"Failed to download URL: {url}")
                return ""

            extracted = await asyncio.to_thread(trafilatura.extract, downloaded)

            if not extracted:
                debug_print("fetch_page_text", f"No extractable content found for URL: {url}")
                return ""

            final_text = extracted[:12000]
            debug_print("fetch_page_text", final_text)
            return final_text

        except Exception as error:
            debug_print("fetch_page_text.error", f"URL: {url} | Error: {error}")
            return ""

    def extract_questions_with_llm(self, topic: str, page_text: str) -> list[dict]:
        """
        Function Name : extract_questions_with_llm
        Description   : Uses the Ollama model to extract interview questions from page text
                        and return them in normalized JSON format.
        Parameters    :
            topic     : Topic to associate with extracted questions
            page_text : Plain text extracted from the web page
        """
        if not page_text.strip():
            debug_print("extract_questions_with_llm", "Empty page text received")
            return []

        prompt = f"""
You are an extraction system.

Task:
Extract only genuine interview questions from the text below.

Rules:
1. Return valid JSON only.
2. Return a JSON array.
3. Each item must be an object with exactly these keys:
   - "topic"
   - "question"
4. Use "{topic}" as the topic unless another topic is clearly better.
5. Keep only actual interview questions.
6. Remove duplicates.
7. Ignore answers, explanations, ads, headings, navigation text, and page boilerplate.
8. Rewrite each question into clean English if needed.
9. If a valid interview item does not end with a question mark, convert it into a proper question.
10. Maximum 20 questions.

Text:
{page_text}
"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json"
                    )
        except Exception as error:
            debug_print("extract_questions_with_llm.error", str(error))
            return []

        content = response["message"]["content"]

        try:
            data = json.loads(content)

        except json.JSONDecodeError:
            debug_print("extract_questions_with_llm", "Invalid JSON returned by model")
            return []

        if isinstance(data, dict):
            # Saw that the output was sometimes a valid question but a dict so added this filter
            if "items" in data and isinstance(data["items"], list):
                data = data["items"]
            elif "questions" in data and isinstance(data["questions"], list):
                data = data["questions"]
            elif "results" in data and isinstance(data["results"], list):
                data = data["results"]
            elif "data" in data and isinstance(data["data"], list):
                data = data["data"]
            else:
                data = [data]

        elif not isinstance(data, list):
            # Neither of above
            debug_print("extract_questions_with_llm", "Model output was neither a dict nor a list")
            return []

        cleaned_questions = []
        seen = set()

        for item in data:
            if not isinstance(item, dict):
                continue

            question = str(item.get("question", "")).strip()
            item_topic = str(item.get("topic", topic)).strip() or topic

            if not question:
                continue

            normalized = re.sub(r"\s+", " ", question).strip()

            if len(normalized) < 10:
                continue

            if not normalized.endswith("?"):
                normalized = normalized + "?"

            normalized_key = normalized.lower()

            if normalized_key in seen:
                continue

            seen.add(normalized_key)
            cleaned_questions.append({
                "topic": item_topic,
                "question": normalized
            })

        debug_print("extract_questions_with_llm.cleaned_questions", cleaned_questions)
        return cleaned_questions

    def build_bulk_operations(self, questions: list[dict], source_url: str) -> list[UpdateOne]:
        """
        Function Name : build_bulk_operations
        Description   : Converts extracted questions into MongoDB bulk upsert operations.
        Parameters    :
            questions  : List of normalized question dictionaries
            source_url : URL from which the questions were extracted
        """
        operations = []

        for item in questions:
            operations.append(
                UpdateOne(
                    {"question": item["question"]},
                    {
                        "$setOnInsert": {
                            "topic": item["topic"],
                            "question": item["question"],
                            "source_url": source_url,
                            "created_at": datetime.now(timezone.utc)
                        },
                        "$set": {
                            "updated_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
            )

        debug_print("build_bulk_operations", f"Total operations built: {len(operations)}")
        return operations

    def save_questions(self, questions: list[dict], source_url: str) -> int:
        """
        Function Name : save_questions
        Description   : Saves extracted questions into MongoDB using bulk upsert operations.
        Parameters    :
            questions  : List of normalized question dictionaries
            source_url : URL from which the questions were extracted
        """
        if not questions:
            debug_print("save_questions", "No questions to save")
            return 0

        operations = self.build_bulk_operations(questions, source_url)

        try:
            result = self.collection.bulk_write(operations, ordered=False)
            inserted_count = result.upserted_count
            debug_print("save_questions", f"Inserted count: {inserted_count}")
            return inserted_count
        except BulkWriteError as error:
            debug_print("save_questions", f"Bulk write warning: {error.details}")
            return 0

    async def process_query(self, query: str):
        """
        Function Name : process_query
        Description   : Searches the web for one topic query, extracts questions from result pages,
                        and stores them in MongoDB.
        Parameters    :
            query : Search query for interview questions
        """
        logging.info("Processing query: %s", query)
        urls = self.search_urls(query)
        debug_print("process_query.urls", urls)

        for url in urls:
            try:
                page_text = await self.fetch_page_text(url)

                if not page_text.strip():
                    continue

                topic = query.replace(" interview questions", "").strip()
                questions = self.extract_questions_with_llm(topic, page_text)
                inserted_count = self.save_questions(questions, url)

                debug_print(
                    "process_query.result",
                    {
                        "query": query,
                        "url": url,
                        "topic": topic,
                        "extracted_questions": len(questions),
                        "inserted_count": inserted_count
                    }
                )
            except Exception as error:
                debug_print("process_query.error", f"Failed URL: {url} | Error: {error}")
                logging.exception("Failed to process URL %s: %s", url, error)

    async def run_once(self):
        """
        Function Name : run_once
        Description   : Executes one full ingestion cycle for all configured interview topics.
        Parameters    :
            None
        """
        for query in TOPIC_QUERIES:
            await self.process_query(query)

        debug_print("run_once", "Completed one ingestion cycle")

    async def run_forever(self, interval_seconds: int):
        """
        Function Name : run_forever
        Description   : Runs the ingestion cycle continuously in the background at fixed intervals.
        Parameters    :
            interval_seconds : Delay between consecutive ingestion cycles in seconds
        """
        while True:
            started_at = datetime.now(timezone.utc)
            debug_print("run_forever.start", f"Cycle started at {started_at.isoformat()}")

            try:
                await self.run_once()
            except Exception as error:
                debug_print("run_forever.error", str(error))
                logging.exception("Ingestion cycle failed: %s", error)

            finished_at = datetime.now(timezone.utc)
            debug_print("run_forever.end", f"Cycle finished at {finished_at.isoformat()}")
            await asyncio.sleep(interval_seconds)


async def main():
    """
    Function Name : main
    Description   : Configures logging, creates the ingestor object, and starts
                    the background ingestion loop.
    Parameters    :
        None
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    debug_print("main", "Starting InterviewQuestionIngestor")

    ingestor = InterviewQuestionIngestor(
        mongo_uri=MONGO_URI,
        database_name=DATABASE_NAME,
        collection_name=COLLECTION_NAME,
        model=MODEL
    )

    await ingestor.run_forever(FETCH_INTERVAL_SECONDS)


if __name__ == "__main__":
    """
    Function Name : __main__
    Description   : Entry point of the script.
    Parameters    :
        None
    """
    debug_print("__main__", "Program execution started")
    asyncio.run(main())