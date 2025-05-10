from dataclasses import dataclass
import json
from textwrap import dedent
import streamlit as st  # Use Streamlit secrets instead of dotenv

from httpx import AsyncClient
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from sqlalchemy import Engine, create_engine, inspect, text
from datetime import datetime
from sqlalchemy.orm import Session


system_prompt = dedent("""
    You are an AI agent equipped with PostGreSQL tools. Your goal is to help users interact with the database and get insights from it.
    To run a SQL, follow these steps:
    1. First, run the 'list_tables' tool to get a list of tables in the database.
    2. Then, run the 'describe_table' tool to get the schema of a specific table from the database.
    3. Then, construct the SQL statement and run the 'run_sql' tool to execute a SQL query on the database.
    4. Finally, analyze the results and provide insights to the user.
""")

@dataclass
class Dependencies:
    db_engine: Engine

class ResponseModel(BaseModel):
    detail: str = Field(name="detail", description="The result of the query.")

custom_http_client = AsyncClient(timeout=30)
model = AnthropicModel(
    'claude-3-5-sonnet-latest',
    provider=AnthropicProvider(api_key=st.secrets["API_KEY"], http_client=custom_http_client),
)

agent = Agent(
    name='Database Insights Agent',
    model=model,
    system_prompt=[system_prompt],
    result_type=ResponseModel,
)

@agent.tool
def list_tables(ctx: RunContext) -> str:
    """
    List all tables in the database.
    """
    print("Listing tables in the database...")
    db_engine = ctx.deps.db_engine
    try:
        table_names = inspect(db_engine).get_table_names()
        return json.dumps(table_names)
    except Exception as e:
        return f"Error listing tables: {e}"

@agent.tool
def describe_table(ctx: RunContext, table_name: str) -> str:
    """
    Describe the schema of a specific table.
    """
    print(f"Describing table: {table_name}")
    db_engine = ctx.deps.db_engine

    try:
        db_inspector = inspect(db_engine)
        table_schema = db_inspector.get_columns(table_name)
        return json.dumps([str(column) for column in table_schema])
    except Exception as e:
        return f"Error describing table {table_name}: {e}"

@agent.tool
def run_sql(ctx: RunContext, sql: str) -> str:
    """
    Run a SQL query on the database.
    """
    print(f"Running SQL query: {sql}")
    db_engine = ctx.deps.db_engine
    with Session(db_engine) as session:
        try:
            result = session.execute(text(sql))
            rows = result.fetchall()
            recordset = [row._asdict() for row in rows]
            return json.dumps(recordset, default=str)
        except Exception as e:
            return f"Error running SQL query: {e}"

@agent.tool
def get_current_date(ctx: RunContext) -> str:
    """
    Get the current date.
    """
    print("Fetching the current date...")
    current_date = datetime.now().strftime("%Y-%m-%d")
    return current_date

if __name__ == "__main__":
    db_engine = create_engine(st.secrets["DATABASE_URL"])  # Use Streamlit secrets
    deps = Dependencies(db_engine=db_engine)

    response = agent.run_sync(
        'Which instruments are nearing their calibration date in the next 30 days?',
        deps=deps,
    )

    print(response.data.detail)
