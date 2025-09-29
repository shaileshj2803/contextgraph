#!/usr / bin / env python3
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))
"""
Social Network Example for igraph - cypher - db.

This example demonstrates building and querying a social network graph
with people, their relationships, and interests.
"""

from contextgraph import GraphDB
import random

def create_social_network():
    """Create a sample social network."""
    db = GraphDB()

    # Define some sample people
    people = [
        {"name": "Alice", "age": 28, "city": "New York", "occupation": "Engineer"},
        {"name": "Bob", "age": 32, "city": "San Francisco", "occupation": "Designer"},
        {"name": "Charlie", "age": 25, "city": "New York", "occupation": "Teacher"},
        {"name": "Diana", "age": 30, "city": "Boston", "occupation": "Doctor"},
        {"name": "Eve", "age": 27, "city": "San Francisco", "occupation": "Engineer"},
        {"name": "Frank", "age": 35, "city": "Chicago", "occupation": "Lawyer"},
        {"name": "Grace", "age": 29, "city": "New York", "occupation": "Artist"},
        {"name": "Henry", "age": 31, "city": "Boston", "occupation": "Engineer"},
    ]

    # Define interests
    interests = [
        "Programming", "Art", "Music", "Sports", "Travel",
        "Cooking", "Reading", "Photography", "Gaming", "Fitness"
    ]

    print("Creating social network...")

    # Create person nodes
    person_ids = {}
    for person in people:
        person_id = db.create_node(labels=["Person"], properties=person)
        person_ids[person["name"]] = person_id
        print(f"  Created person: {person['name']}")

    # Create interest nodes
    interest_ids = {}
    for interest in interests:
        interest_id = db.create_node(
            labels=["Interest"],
            properties={"name": interest}
        )
        interest_ids[interest] = interest_id
        print(f"  Created interest: {interest}")

    # Create friendships (random connections)
    friendships = [
        ("Alice", "Bob", "college"),
        ("Alice", "Charlie", "work"),
        ("Bob", "Eve", "work"),
        ("Charlie", "Diana", "school"),
        ("Diana", "Henry", "work"),
        ("Eve", "Frank", "gym"),
        ("Frank", "Grace", "neighborhood"),
        ("Grace", "Henry", "art_class"),
        ("Alice", "Grace", "mutual_friend"),
        ("Bob", "Charlie", "conference"),
    ]

    for person1, person2, context in friendships:
        db.create_relationship(
            person_ids[person1],
            person_ids[person2],
            "FRIENDS_WITH",
            {"context": context, "strength": random.choice(["weak", "medium", "strong"])}
        )
        print(f"  Created friendship: {person1} <-> {person2} (via {context})")

    # Create interest relationships (random assignments)
    for person_name, person_id in person_ids.items():
        # Each person has 2 - 4 interests
        person_interests = random.sample(interests, random.randint(2, 4))
        for interest in person_interests:
            db.create_relationship(
                person_id,
                interest_ids[interest],
                "INTERESTED_IN",
                {"level": random.choice(["casual", "moderate", "passionate"])}
            )
        print(f"  Added interests for {person_name}: {', '.join(person_interests)}")

    return db

def demonstrate_queries(db):
    """Demonstrate various queries on the social network."""
    print("\n=== Social Network Queries ===\n")

    # Query 1: Find all people
    print("1. All people in the network:")
    people = db.find_nodes(labels=["Person"])
    for person in people:
        props = person["properties"]
        print(f"   - {props['name']}, {props['age']}, {props['city']} ({props['occupation']})")
    print(f"   Total: {len(people)} people\n")

    # Query 2: Find people by city
    print("2. People in New York:")
    ny_people = db.find_nodes(labels=["Person"], properties={"city": "New York"})
    for person in ny_people:
        print(f"   - {person['properties']['name']}")
    print(f"   Total: {len(ny_people)} people\n")

    # Query 3: Find people by occupation
    print("3. Engineers in the network:")
    engineers = db.find_nodes(labels=["Person"], properties={"occupation": "Engineer"})
    for person in engineers:
        props = person["properties"]
        print(f"   - {props['name']} in {props['city']}")
    print(f"   Total: {len(engineers)} engineers\n")

    # Query 4: Find all friendships
    print("4. All friendships:")
    friendships = db.find_relationships(rel_type="FRIENDS_WITH")
    for friendship in friendships:
        source = db.get_node(friendship["source"])
        target = db.get_node(friendship["target"])
        context = friendship["properties"]["context"]
        strength = friendship["properties"]["strength"]
        print(f"   - {source['properties']['name']} <-> {target['properties']['name']} "
              f"(via {context}, {strength})")
    print(f"   Total: {len(friendships)} friendships\n")

    # Query 5: Find strong friendships
    print("5. Strong friendships:")
    strong_friendships = db.find_relationships(
        rel_type="FRIENDS_WITH",
        properties={"strength": "strong"}
    )
    for friendship in strong_friendships:
        source = db.get_node(friendship["source"])
        target = db.get_node(friendship["target"])
        print(f"   - {source['properties']['name']} <-> {target['properties']['name']}")
    print(f"   Total: {len(strong_friendships)} strong friendships\n")

    # Query 6: Find interests and who has them
    print("6. Popular interests:")
    interests = db.find_nodes(labels=["Interest"])
    interest_popularity = {}

    for interest in interests:
        interest_name = interest["properties"]["name"]
        interested_people = db.find_relationships(
            rel_type="INTERESTED_IN",
            properties={}  # Find all INTERESTED_IN relationships
        )

        # Count how many people are interested in this specific interest
        count = 0
        for rel in interested_people:
            if rel["target"] == interest["id"]:
                count += 1

        interest_popularity[interest_name] = count

    # Sort by popularity
    sorted_interests = sorted(interest_popularity.items(), key=lambda x: x[1], reverse=True)
    for interest, count in sorted_interests:
        print(f"   - {interest}: {count} people")
    print()

    # Query 7: Find people with shared interests
    print("7. People with shared interests (example: Programming):")
    programming_interest = None
    for interest in interests:
        if interest["properties"]["name"] == "Programming":
            programming_interest = interest
            break

    if programming_interest:
        programming_rels = db.find_relationships(rel_type="INTERESTED_IN")
        programmers = []
        for rel in programming_rels:
            if rel["target"] == programming_interest["id"]:
                person = db.get_node(rel["source"])
                programmers.append(person["properties"]["name"])

        print(f"   People interested in Programming: {', '.join(programmers)}")
    print()

def main():
    """Main function to run the social network example."""
    print("=== Social Network Example ===\n")

    # Create the social network
    db = create_social_network()

    print("\nSocial network created!")
    print(f"Total nodes: {db.node_count}")
    print(f"Total relationships: {db.relationship_count}")

    # Demonstrate queries
    demonstrate_queries(db)

    # Save the network
    print("8. Saving the social network...")
    db.save("social_network.json")
    print("   Social network saved to 'social_network.json'")

    print("\n=== Social Network Example completed! ===")
    print("You can load this network later using:")
    print("  db = GraphDB()")
    print("  db.load('social_network.json')")

if __name__ == "__main__":
    main()
