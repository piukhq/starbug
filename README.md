# Starbug

Starbug is a testing framework for Bink Applications which aims to abstract Kubernetes complexities from testing requirements.

## API Documentation

### Testing Functionality

<details>
<summary><code>GET /test</code> - Get all tests</summary>

###### Parameters
> None

###### Body
> None

###### Responses
> | http code     | content-type                      | response            |
> |---------------|-----------------------------------|---------------------|
> | `200`         | `application/json;charset=UTF-8`  | JSON object         |
</details>


<details>
<summary><code>GET /test/{test_name}</code> - Get a specific test</summary>

###### Parameters
> | name              |  type     | data type      | description            |
> |-------------------|-----------|----------------|------------------------|
> | `test_name`       |  required | string         | The specific test name |

###### Body
> None

###### Responses
> | http code     | content-type        | response                          |
> |---------------|---------------------|-----------------------------------|
> | `200`         | `application/json`  | JSON object                       |
> | `404`         | `application/json`  | `{"error":"Not Found"}`           |
</details>


<details>
<summary><code>POST /test</code> - Create a Test</summary>

###### Parameters
> None

###### Body
> ```json
> {
>    "infrastructure": [ // Required: Infrastructure components to create for the test
>        {
>             "name": "postgres", // Required: Name of the required infrastructure component
>             "image": "docker.io/postgres:16" // Optional: Override the default tag used for this component
>        },
>        {"name": "rabbitmq"},
>        {"name": "redis"}
>    ],
>    "applications": [ // Required: Applications to Deploy
>        {"name": "angelia"}
>        {"name": "hermes"}
>        {"name": "midas"}
>    ],
>    "test": {"name": "kiroshi"} // Required: The test to run
> }
> ```

###### Responses
> | http code     | content-type                      | response            |
> |---------------|-----------------------------------|---------------------|
> | `200`         | `application/json;charset=UTF-8`  | JSON object         |
> | `500`         | `application/json;charset=UTF-8`  | JSON object         |
</details>

<details>
<summary><code>DELETE /test/{test_name}</code> - Delete a specific test</summary>

###### Parameters
> | name              |  type     | data type      | description            |
> |-------------------|-----------|----------------|------------------------|
> | `test_name`       |  required | string         | The specific test name |

###### Responses
> | http code     | content-type                      | response                |
> |---------------|-----------------------------------|-------------------------|
> | `202`         | `application/json;charset=UTF-8`  | JSON object             |
> | `404`         | `application/json;charset=UTF-8`  | `{"error":"Not Found"}` |
</details>
