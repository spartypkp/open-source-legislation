import tiktoken
import psycopg
import json
import os
import concurrent.futures
import sys
import anthropic
from psycopg.rows import class_row, dict_row
from typing import Optional, List, Any, Dict, Callable, Tuple
from openai import OpenAI
from anthropic import Anthropic
from anthropic.types import MessageParam
import instructor
import pydantic
from pydantic import BaseModel, Field, model_validator
from utils.pydanticModels import APIParameters, ChatMessage, APIUsage
from datetime import datetime
import time


DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)

from dotenv import load_dotenv
import os


# ==== Set API Keys ====

OPENAI_API_KEY_NAME = "Personal Key"
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

ANTHROPIC_API_KEY_NAME = "Personal Key"
anthropic_client = Anthropic(
    api_key=os.getenv("OPENAI_API_KEY")
)


instructor_client = instructor.patch(OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
))




    

def main():
    pass   
    
    

def convert_to_messages(user: str, system: Optional[str] = None) -> List[ChatMessage]:
    """
    Converts a user string and an optional system string into a list of ChatMessage objects.

    This function is primarily used for preparing data to be used with the OpenAI or Anthropic AI.

    Args:
    user (str): The user's message. This will be converted into a ChatMessage with role 'user'.
    system (Optional[str]): An optional system message. If provided, this will be converted into a ChatMessage with role 'system'. Defaults to None. Not required for Anthropic.

    Returns:
    List[ChatMessage]: A list of ChatMessage objects. If a system message was provided, the list will contain two messages: the system message followed by the user message. Otherwise, the list will contain only the user message.
    """
    messages = []
    if system:
        messages.append(ChatMessage(role="system", content=system))
    messages.append(ChatMessage(role="user", content=user))
    return messages


def create_chat_completion(params: APIParameters, user: Optional[str] = None, insert_usage: bool = True ) -> Tuple[str, APIUsage]:
    """
    Routes the chat completion request to the appropriate vendor's API based on the vendor specified in the parameters.

    Args:
        params (APIParameters): The parameters for the API call as the APIParameters Pydantic Model.
        user (str, optional): The requesting user's DB name. Defaults to None.
        insert_usage (bool, optional): Flag to determine if usage data should be inserted. Defaults to True.

    Raises:
        ValueError: If an unsupported vendor is provided or if user is not provided when insert_usage is True.

    Returns:
        Tuple[str, APIUsage]: The chat completion response and usage data.
    """
    if params.vendor.lower() == 'openai':
        response_tuple = create_chat_completion_openai(params)
    elif params.vendor.lower() == 'instructor':
        response_tuple = create_chat_completion_instructor(params)
    elif params.vendor.lower() == 'anthropic':
        response_tuple =  create_chat_completetion_anthropic(params)
    else:
        raise ValueError("Unsupported vendor")
    
    if insert_usage:
        if user is None:
            raise ValueError("User must be provided to insert usage data!")
        response_tuple[1].insert(user=user)
    return response_tuple

def create_chat_completion_openai(params: APIParameters) -> Tuple[str, APIUsage]:
    """
    Calls the OpenAI ChatCompletion API and returns the completion message and usage data.

    Args:
        params (APIParameters): The parameters for the API call as the APIParameters Pydantic Model.

    Returns:
        Tuple[str, APIUsage]: The chat completion response and usage data.
    """
    start = time.time()
    try:
        # Additional check for response_format presence
        response_format = params.response_format or None
        
        completion = openai_client.chat.completions.create(
            model=params.model,
            messages=params.messages,
            temperature=params.temperature,
            top_p=params.top_p,
            frequency_penalty=params.frequency_penalty,
            presence_penalty=params.presence_penalty,
            stream=params.stream,
            response_format=response_format  # Use response_format if provided
        )

        if not completion:
            raise Exception(f"OpenAI API call failed with status: {completion}")
        
        status = 200
        response_id = completion.id
        error_message = None
        duration = time.time() - start
        content: str = completion.choices[0].message.content

        usage = completion.usage

        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

    except Exception as error:
        print(f"Error: {error}")
        status = 400
        error_message = str(error)
        duration = None
        content = None
        input_tokens, output_tokens, total_tokens = None, None, None
        response_id = None

    usage = APIUsage(model=params.model, 
                    vendor=params.vendor, 
                    response_id=response_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    status=status,
                    error_message=error_message,
                    calling_function=params.calling_function,
                    timestamp=datetime.now(),
                    duration=duration,
                    api_key_name=OPENAI_API_KEY_NAME
                    )

    return content, usage

# Calls the Anthropic ChatCompletion API and returns the completion message
def create_chat_completetion_anthropic(params: APIParameters) -> Tuple[str, APIUsage]:
    """
    Calls the Anthropic ChatCompletion API and returns the completion message and usage data.

    Args:
        params (APIParameters): The parameters for the API call as the APIParameters Pydantic Model.

    Returns:
        Tuple[str, APIUsage]: The chat completion response and usage data.
    """
    start = time.time()
    
    try:
        if params.messages[0].role != "system":
            system = None
            messages = params.messages
        else:
            system = params.messages.pop(0)
            messages = params.messages

        completion = anthropic_client.messages.create(
            model=params.model,
            system = system,
            max_tokens=params.max_tokens,
            stream=params.stream,
            temperature=params.temperature,
            top_p=params.top_p,
            messages=messages
            
        )
        if not completion:
            raise Exception(f"Anthropic API call failed with status: {completion}")
        
        usage = completion.usage
        
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        total_tokens = usage.total_tokens

        status = 200
        error_message = None
        duration = time.time() - start
        content = completion.content[0]['text']
        response_id = completion.id

    except Exception as error:
        status = 400
        error_message = str(error)
        print(f"Error: {error}")
        duration = None
        content = None
        response_id = None
        input_tokens, output_tokens, total_tokens = None, None, None

    
    usage = APIUsage(model=params.model, 
                    vendor=params.vendor, 
                    response_id=response_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    status=status,
                    error_message=error_message,
                    calling_function=params.calling_function,
                    timestamp=datetime.now(),
                    duration=duration,
                    api_key_name=ANTHROPIC_API_KEY_NAME
                    )

    return content, usage

# Calls the Instructor ChatCompletion API and returns the completion message and usage data
def create_chat_completion_instructor(params: APIParameters) -> Tuple[str, APIUsage]:
    """
    Calls the Instructor ChatCompletion API and returns the completion message and usage data.

    Args:
        params (APIParameters): The parameters for the API call as the APIParameters Pydantic Model.

    Returns:
        Tuple[str, APIUsage]: The chat completion response and usage data.
    """
    start = time.time()
    try:
        # Additional check for response_format presence
        
        completion = instructor_client.chat.completions.create(
            model=params.model,
            response_model=params.response_model,
            max_retries=params.max_retries,
            messages=params.messages,
            temperature=params.temperature,
            top_p=params.top_p,
            frequency_penalty=params.frequency_penalty,
            presence_penalty=params.presence_penalty,
            stream=params.stream,
        )

        if not completion:
            raise Exception(f"Instructor OpenAI API call failed with status: {completion}")
        
        status = 200
        response_id = completion._raw_response.id
        error_message = None
        duration = time.time() - start
        content: str = completion.choices[0].message.content

        usage = completion._raw_response.usage

        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

    except Exception as error:
        print(f"Error: {error}")
        status = 400
        error_message = str(error)
        duration = None
        content = None
        input_tokens, output_tokens, total_tokens = None, None, None
        response_id = None
    

    usage = APIUsage(model=params.model, 
                    vendor=params.vendor, 
                    response_id=response_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    status=status,
                    error_message=error_message,
                    calling_function=params.calling_function,
                    timestamp=datetime.now(),
                    duration=duration,
                    api_key_name=OPENAI_API_KEY_NAME
                    )

    return content, usage




    
# Creates a vector embedding from a string of text
def create_embedding(input_text):
    """Create an embedding from a string of text."""
    response = openai_client.embeddings.create(
        input=input_text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
     

# ===== Database Functions =====
def db_connect(row_factory=None):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_username = os.getenv("DB_USERNAME")
        db_password = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT")

        conn = psycopg.connect(dbname=db_name,host=db_host,user=db_username,password=db_password,port=db_port,client_encoding="utf8")
        
            
		
        if row_factory is not None:
            conn.row_factory = row_factory
        return conn
    except (Exception, psycopg.DatabaseError) as error:
        print(error)
        raise error


def pydantic_select(sql_select: str, modelType: Any) -> List[Any]:
    """
    Executes a SQL SELECT statement and returns the result rows as a list of Pydantic models.

    Args:
        sql_select (str): The SQL SELECT statement to execute.
        modelType (Optional[Any]): The Pydantic model to use for the row factory
        user (Optional[str]): The user making the request

    Returns:
        List[Any]: The rows returned by the SELECT statement as a list of Pydantic Models.
    """   
    # Use the provided modelType (PydanticModel) for the row factory
    if modelType:
        conn = db_connect(row_factory=class_row(modelType))
    

    cur = conn.cursor()

    # Execute the SELECT statement
    cur.execute(sql_select)

    # Fetch all rows
    rows = cur.fetchall()
    

    # Close the cursor and the connection
    cur.close()
    conn.close()

    return rows

def regular_select(sql_select: str, ) -> List[Dict[str, Any]]:
    """
    Executes a SQL SELECT statement and returns the result rows as List of dictionaries.

    Args:
        sql_select (str): The SQL SELECT statement to execute..
        user (Optional[str]): The user making the request

    Returns:
        List[str, Any]: The rows returned by the SELECT statement as a List of Dictionaries.
    """   
    # If they provide a pydantic model, use it for the row factory
    conn = db_connect(row_factory=dict_row)

    cur = conn.cursor()

    # Execute the SELECT statement
    cur.execute(sql_select)

    # Fetch all rows
    rows = cur.fetchall()
    

    # Close the cursor and the connection
    cur.close()
    conn.close()

    return rows


def pydantic_insert(table_name: str, models: List[Any]):
    """
    Inserts the provided List of Pydantic Models into the specified table.

    Args:
        table_name (str): The name of the table to insert into.
        nodes (List[Any]): The list of Pydantic Models to insert.
        user (str): The user making the request.
    """
    # Get the psycopg3 connection object
    conn = db_connect()

    with conn.cursor() as cursor:
        for model in models:
            # Convert the NodeModel to a dictionary and exclude default values
            
            model_dict = model.model_dump(mode="json",exclude_defaults=True)

            for key, value in model_dict.items():
                if type(value) == dict:
                    model_dict[key] = json.dumps(value)

            # 
            

            # Prepare the column names and placeholders
            columns = ', '.join(model_dict.keys())
            placeholders = ', '.join(['%s'] * len(model_dict))

            

            # Create the INSERT statement using psycopg.sql to safely handle identifiers
            query = psycopg.sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(columns),
                psycopg.sql.SQL(placeholders)
            )

            # Execute the INSERT statement
            cursor.execute(query, tuple(model_dict.values()))

    # Commit the changes
    conn.commit()
    conn.close()

def regular_insert(table_name: str, dicts: List[Dict[str, Any]]):
    """
    Inserts the provided List of Dictionaries into the specified table.

    Args:
        table_name (str): The name of the table to insert into.
        dicts (List[Dict[str, Any]]): The list of dictionaries to insert.
        user (str): The user making the request.
    """
    # Get the psycopg3 connection object
    conn = db_connect()

    with conn.cursor() as cursor:
        for d in dicts:
            # Convert the NodeModel to a dictionary and exclude default values
            
            

            # Prepare the column names and placeholders
            columns = ', '.join(d.keys())
            placeholders = ', '.join(['%s'] * len(d))

            

            # Create the INSERT statement using psycopg.sql to safely handle identifiers
            query = psycopg.sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(columns),
                psycopg.sql.SQL(placeholders)
            )

            # Execute the INSERT statement
            cursor.execute(query, tuple(d.values()))

    # Commit the changes
    conn.commit()
    conn.close()


def pydantic_update(table_name: str, models: List[Any], where_field: str, update_columns: Optional[List[str]] = None ):
    """
    Updates the specified table with the provided List of Pydantic Models.

    Args:
        table_name (str): The name of the table to update.
        nodes (List[PydanticModel]): The nodes to use for the update.
        where_field (str): The field to use in the WHERE clause of the update statement.
        update_columns (Optional[List[str]]): The columns to include in the update. If None, all fields are included. Defaults to None.
        user (Optional[str]): The user making the request. Defaults to None.
    """
    conn = db_connect()

    with conn.cursor() as cursor:
        for model in models:
            # Convert the NodeModel to a dictionary and exclude where field, include values to update only
            if update_columns:
                model_dict = model.model_dump(mode="json",exclude_defaults=True, include=update_columns)
            else:
                model_dict = model.model_dump(mode="json",exclude_defaults=True)

            for key, value in model_dict.items():
                if type(value) == dict:
                    model_dict[key] = json.dumps(value)
            
            where_value = model_dict[where_field]
            # print(where_value)
            del model_dict[where_field]

            # Prepare the column names and placeholders
            set_statements = ', '.join([f"{column} = %s" for column in model_dict.keys()])
            
            query = psycopg.sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(set_statements),
                psycopg.sql.Identifier(where_field)
            )
            # print(query.as_string(conn))
            # Execute the UPDATE statement
            cursor.execute(query, tuple(list(model_dict.values()) + [where_value]))
    conn.commit()
    conn.close

def regular_update(table_name: str, dicts: List[Any], where_field: str, update_columns: Optional[List[str]] = [] ):
    """
    Updates the specified table with the provided List of Dictionaries.

    Args:
        table_name (str): The name of the table to update.
        dicts (List[Dict[str, Any]]): The List of Dictionaries to use for the update.
        where_field (str): The field to use in the WHERE clause of the update statement.
        update_columns (Optional[List[str]]): The columns to include in the update. If None, all fields are included. Defaults to []
        user (Optional[str]): The user making the request
    """
    conn = db_connect()

    with conn.cursor() as cursor:
        for d in dicts:
            # exclude where field, include values to update only
            where_value = d[where_field]
            del d[where_field]

            for column in update_columns:
                if column not in d:
                    del d[column]

            for key, value in d.items():
                if type(value) == dict:
                    d[key] = json.dumps(value)
            
            

            # Prepare the column names and placeholders
            set_statements = ', '.join([f"{column} = %s" for column in d.keys()])
            
            query = psycopg.sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(set_statements),
                psycopg.sql.Identifier(where_field)
            )
            # print(query.as_string(conn))
            # Execute the UPDATE statement
            cursor.execute(query, tuple(list(d.values()) + [where_value]))
    conn.commit()
    conn.close


def pydantic_upsert(table_name: str, models: List[Any], where_field: str):
    """
    Performs an upsert operation on the specified table with the provided list of Pydantic Models.

    Args:
        table_name (str): The name of the table to upsert into.
        nodes (List[PydanticModels]): The list of pydantic models to use for the upsert.
        where_field (str): The field to use in the WHERE clause of the update statement.
        user (Optional[str]): The user making the request. 
    """
    for model in models:
        try:
            pydantic_insert(table_name=table_name, models=[model])
        except psycopg.errors.UniqueViolation:
            pydantic_update(table_name=table_name, models=[model], where_field=where_field)

def regular_upsert(table_name: str, dicts: List[Any], where_field: str):
    """
    Performs an upsert operation on the specified table with the provided list of dictionaries.

    Args:
        table_name (str): The name of the table to upsert into.
        dicts (List[Dict[str, Any]]): The list of dictionaries to use for the upsert.
        where_field (str): The field to use in the WHERE clause of the update statement.
        user (Optional[str]): The user making the request.
    """
    for d in dicts:
        try:
            regular_insert(table_name=table_name, dicts=[d])
        except psycopg.errors.UniqueViolation as e:
            regular_update(table_name=table_name, dicts=[d], where_field=where_field)





# ===== Cost Estimation Functions =====
def anthropic_estimate_tokens(prompt) -> int:
    """Returns the number of tokens in a text string."""
    count = anthropic_client.count_tokens(prompt)
    return count


def openai_estimate_tokens(string) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens



# ===== Async & Concurrent Functions =====
def run_concurrently(main_func: Callable, args_list: List[Any], batch_size: int):
    """
    Concurrently runs a function with a list of arguments in batches.
    Args:
        main_func (Callable): The function to run.
        args_list (List[Any]): The list of arguments to use for the function.
        batch_size (int): The number of arguments to include in each batch.
    Returns:
        List[Any]: The results of the function calls.
    """
    results = []
    for i in range(0, len(args_list), batch_size):
        batch = args_list[i:i+batch_size]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(main_func, *args) for args in batch]
        results.extend([future.result() for future in futures])
        print(f"\n=== Batch {(i+batch_size)/batch_size} completed ===\n")

    return results








if __name__ == "__main__":
    main()



