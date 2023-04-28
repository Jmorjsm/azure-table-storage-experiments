import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="HttpTrigger1")
@app.route(route="hello") # HTTP Trigger
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("HttpTrigger1 function processed a request!!!")


@app.function_name(name="results")
@app.route(route="results")
def results(req func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("getting the results")
