"""Example plugin: demonstrates the plugin register API."""

def register(executor):
    # Example: extend executor with a custom command
    def hello_world():
        return "Hello from example plugin!"
    # We inject a method (simple demo)
    setattr(executor, "hello_plugin", hello_world)
