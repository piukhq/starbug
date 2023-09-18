# Starbug

## Example JSON Request

```json
# POST /test
{
	"infrastructure": [
		{"name": "postgres", "image": "docker.io/postgres:14"},
		{"name": "redis"},
		{"name": "rabbitmq"}
	],
	"applications": [
		{"name": "hermes"},
		{"name": "harmonia"}
	],
	"test_suite": {"name": "atalanta"}
}
```
