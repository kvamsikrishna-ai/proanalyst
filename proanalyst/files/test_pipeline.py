import csv
from rag import get_rag_components, answer_query

QUESTIONS = [
    "What OAuth 2.0 grant types does Upwork support?",
    "How long does an access token last?",
    "How long is a refresh token valid?",
    "Which grant type is available only for enterprise accounts?",
    "What endpoint do I call to get an authorization code?",
    "What is the token endpoint for Upwork?",
    "What header do I need to specify organization context?",
    "What happens if I don't send the X-Upwork-API-TenantId header?",
    "How do I get the value for the X-Upwork-API-TenantId header?",
    "What parameters are required for the Authorization Code Grant token request?",
    "Does Upwork's GraphQL API return HTTP 400 for bad requests?",
    "What are the three components of a GraphQL error response in Upwork?",
    "When does Upwork return a 5XX HTTP status code?",
    "What error classification appears when you query a field without required arguments?",
    "If I don't have the right OAuth scopes, what HTTP status code will I get?",
    "What permission is required to query a job posting by ID?",
    "What GraphQL query do I use to fetch a single job posting?",
    "What is the difference between jobPosting and marketplaceJobPosting?",
    "Is marketplaceJobPostings still recommended to use?",
    "How do I fetch job posting content for multiple IDs at once?",
    "Who can create subscriptions on the Upwork API?",
    "What happens after a subscription is created?",
    "What three fields does a subscription event payload contain?",
    "What entity types can I subscribe to?",
    "What actions can I subscribe to for job postings?",
    "What permissions do I need to query the list of countries?",
    "What fields are returned in the languages query?",
    "What is the reasons query used for?",
    "Can service accounts perform write operations?",
    "How do you assign permissions to a service account?",
    "Are service accounts available to all Upwork users?",
    "What is the rate limit for Upwork API calls?",
    "How do I search for freelancers via the API?",
    "What is the price of an Upwork enterprise plan?",
    "Can I use the Implicit Grant to get a refresh token?",
    "What scopes are available for the Upwork API?"
]


def main():
    print("Loading RAG components...")
    retriever, llm = get_rag_components()

    results = []

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\n[{i}/{len(QUESTIONS)}] {question}")

        try:
            result = answer_query(
                query=question,
                retriever=retriever,
                llm=llm
            )

            answer = result["answer"]
            latency = round(result["latency"], 2)

            print(f"Latency: {latency}s")
            print(f"Answer: {answer[:200]}...")

            results.append({
                "question": question,
                "answer": answer,
                "latency_seconds": latency
            })

        except Exception as e:
            print(f"ERROR: {e}")

            results.append({
                "question": question,
                "answer": f"ERROR: {str(e)}",
                "latency_seconds": -1
            })

    with open("rag_test_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "question",
                "answer",
                "latency_seconds"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print("\nDone.")
    print("Results saved to rag_test_results.csv")

    successful = [
        r["latency_seconds"]
        for r in results
        if r["latency_seconds"] > 0
    ]

    if successful:
        avg_latency = sum(successful) / len(successful)
        print(f"Average Latency: {avg_latency:.2f}s")


if __name__ == "__main__":
    main()