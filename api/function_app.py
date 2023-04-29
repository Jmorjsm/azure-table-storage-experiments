import json
import os

import azure.functions as func
from azure.data.tables import TableClient

app = func.FunctionApp()


@app.function_name(name="results")
@app.route(route="results")
def results(req: func.HttpRequest) -> func.HttpResponse:
    connection_string = os.environ.get("STORAGE_CONNECTION", "UseDevelopmentStorage=true")
    table_name = "results"
    results_array = []
    with TableClient.from_connection_string(connection_string, table_name) as table_client:
        queried_entities = table_client.query_entities()
        for entity in queried_entities:
            results_array.append(entity)

    return func.HttpResponse(json.dumps(results_array))
