
from Agent_pipeline import workflow 


while True:
    user_input = input("Enter your query (or 'exit' to quit): ")
    if user_input.lower() == 'exit':
        break

    initial_state = {
        "user_input": user_input
    }

    result = workflow.invoke(initial_state)
    print("\n" + "=" * 60)
    print("SELECTED ROUTE:", result["route"])
    print("=" * 60)
    print("\nANSWER:\n")
    print(result["answer"])


