#!/usr/bin/env python3
"""
Graph Visualization Example for igraph-cypher-db

This example demonstrates the comprehensive graph visualization capabilities
of igraph-cypher-db, including:

- Multiple visualization backends (matplotlib, plotly, graphviz)
- Different layout algorithms
- Node and edge styling based on properties
- Interactive exploration
- Query result visualization
- Path visualization

Note: This example requires optional visualization dependencies.
Run: pip install matplotlib networkx plotly graphviz
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import contextgraph
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextgraph import GraphDB, GraphVisualizer, install_dependencies


def create_sample_network(db):
    """Create a rich sample network for visualization."""
    print("Creating sample network...")
    
    # Create people with various properties
    people_data = [
        ('Alice', 'Engineer', 'TechCorp', 85000, 28, 'San Francisco'),
        ('Bob', 'Designer', 'TechCorp', 75000, 26, 'San Francisco'),
        ('Charlie', 'Manager', 'TechCorp', 95000, 35, 'San Francisco'),
        ('Diana', 'Developer', 'StartupInc', 80000, 29, 'New York'),
        ('Eve', 'Analyst', 'StartupInc', 70000, 24, 'New York'),
        ('Frank', 'CEO', 'StartupInc', 150000, 42, 'New York'),
        ('Grace', 'Consultant', 'Freelance', 90000, 31, 'Remote'),
        ('Henry', 'Researcher', 'University', 65000, 33, 'Boston'),
        ('Ivy', 'Student', 'University', 0, 22, 'Boston'),
        ('Jack', 'Professor', 'University', 85000, 45, 'Boston'),
    ]
    
    person_ids = {}
    for name, role, company, salary, age, location in people_data:
        person_id = db.create_node(['Person'], {
            'name': name,
            'role': role,
            'company': company,
            'salary': salary,
            'age': age,
            'location': location
        })
        person_ids[name] = person_id
    
    # Create companies
    companies_data = [
        ('TechCorp', 'Technology', 'San Francisco', 500),
        ('StartupInc', 'Technology', 'New York', 50),
        ('University', 'Education', 'Boston', 10000),
        ('Freelance', 'Services', 'Remote', 1),
    ]
    
    company_ids = {}
    for name, industry, location, size in companies_data:
        company_id = db.create_node(['Company'], {
            'name': name,
            'industry': industry,
            'location': location,
            'size': size
        })
        company_ids[name] = company_id
    
    # Create relationships with various types and properties
    relationships = [
        # Professional relationships
        ('Alice', 'Bob', 'WORKS_WITH', {'since': 2020, 'strength': 8}),
        ('Bob', 'Charlie', 'REPORTS_TO', {'since': 2019, 'strength': 7}),
        ('Charlie', 'Alice', 'MANAGES', {'since': 2021, 'strength': 9}),
        ('Diana', 'Eve', 'MENTORS', {'since': 2022, 'strength': 6}),
        ('Frank', 'Diana', 'MANAGES', {'since': 2020, 'strength': 8}),
        ('Frank', 'Eve', 'MANAGES', {'since': 2021, 'strength': 7}),
        
        # Social relationships
        ('Alice', 'Diana', 'KNOWS', {'since': 2018, 'strength': 5}),
        ('Bob', 'Grace', 'FRIENDS', {'since': 2017, 'strength': 9}),
        ('Grace', 'Henry', 'COLLABORATES', {'since': 2019, 'strength': 6}),
        ('Henry', 'Jack', 'COLLEAGUES', {'since': 2015, 'strength': 8}),
        ('Jack', 'Ivy', 'SUPERVISES', {'since': 2023, 'strength': 7}),
        ('Ivy', 'Henry', 'STUDIES_WITH', {'since': 2023, 'strength': 5}),
        
        # Cross-company connections
        ('Charlie', 'Frank', 'PARTNERS_WITH', {'since': 2022, 'strength': 4}),
        ('Grace', 'Alice', 'CONSULTS_FOR', {'since': 2021, 'strength': 6}),
        ('Henry', 'Frank', 'ADVISES', {'since': 2020, 'strength': 5}),
        
        # Self-reference for demonstration
        ('Alice', 'Alice', 'SELF_IMPROVES', {'since': 2020, 'strength': 10}),
    ]
    
    for person1, person2, rel_type, properties in relationships:
        db.create_relationship(person_ids[person1], person_ids[person2], rel_type, properties)
    
    # Employment relationships
    for name, role, company, salary, age, location in people_data:
        db.create_relationship(person_ids[name], company_ids[company], 'WORKS_FOR')
    
    print(f"Created {db.node_count} nodes and {db.relationship_count} relationships")
    return person_ids, company_ids


def demonstrate_basic_visualization(db):
    """Demonstrate basic visualization capabilities."""
    print("\n" + "="*60)
    print("BASIC VISUALIZATION")
    print("="*60)
    
    try:
        # Simple visualization
        print("\n1. Basic graph visualization:")
        fig = db.visualize(
            title="Sample Network - Basic View",
            node_labels=True,
            layout='spring'
        )
        print("✓ Created basic visualization")
        
        # With node sizing based on salary
        print("\n2. Node sizing based on salary:")
        fig = db.visualize(
            title="Network - Node Size by Salary",
            node_size_property='salary',
            node_labels=True,
            layout='spring'
        )
        print("✓ Created visualization with salary-based node sizing")
        
        # With node coloring based on company
        print("\n3. Node coloring based on company:")
        fig = db.visualize(
            title="Network - Colored by Company",
            node_color_property='company',
            node_labels=True,
            layout='circular'
        )
        print("✓ Created visualization with company-based coloring")
        
    except Exception as e:
        print(f"⚠️  Basic visualization failed: {e}")
        print("This might be due to missing dependencies. Run install_dependencies() for help.")


def demonstrate_different_backends(db):
    """Demonstrate different visualization backends."""
    print("\n" + "="*60)
    print("DIFFERENT VISUALIZATION BACKENDS")
    print("="*60)
    
    visualizer = GraphVisualizer(db)
    
    # Check available backends
    print(f"Available backends: {visualizer.available_backends}")
    
    for backend in visualizer.available_backends:
        try:
            print(f"\n{backend.upper()} Backend:")
            fig = visualizer.plot(
                backend=backend,
                title=f"Network Visualization - {backend.title()}",
                node_labels=True,
                node_color_property='age',
                layout='spring'
            )
            print(f"✓ Successfully created {backend} visualization")
            
        except Exception as e:
            print(f"⚠️  {backend} backend failed: {e}")


def demonstrate_different_layouts(db):
    """Demonstrate different layout algorithms."""
    print("\n" + "="*60)
    print("DIFFERENT LAYOUT ALGORITHMS")
    print("="*60)
    
    layouts = ['spring', 'circular', 'random', 'shell', 'kamada_kawai']
    
    for layout in layouts:
        try:
            print(f"\n{layout.upper()} Layout:")
            fig = db.visualize(
                title=f"Network - {layout.title()} Layout",
                layout=layout,
                node_labels=True,
                node_color_property='location'
            )
            print(f"✓ Successfully created {layout} layout")
            
        except Exception as e:
            print(f"⚠️  {layout} layout failed: {e}")


def demonstrate_advanced_styling(db):
    """Demonstrate advanced styling options."""
    print("\n" + "="*60)
    print("ADVANCED STYLING OPTIONS")
    print("="*60)
    
    try:
        # Multiple property styling
        print("\n1. Multi-property styling:")
        fig = db.visualize(
            title="Network - Multi-Property Styling",
            node_size_property='salary',
            node_color_property='age',
            edge_width_property='strength',
            node_labels=True,
            edge_labels=True,
            layout='spring'
        )
        print("✓ Created visualization with multiple property styling")
        
        # Focus on specific node types
        print("\n2. Company-focused view:")
        # This would ideally filter to show only companies and their connections
        fig = db.visualize(
            title="Company Network",
            node_color_property='industry',
            node_size_property='size',
            node_labels=True,
            layout='circular'
        )
        print("✓ Created company-focused visualization")
        
    except Exception as e:
        print(f"⚠️  Advanced styling failed: {e}")


def demonstrate_query_visualization(db):
    """Demonstrate visualization of query results."""
    print("\n" + "="*60)
    print("QUERY RESULT VISUALIZATION")
    print("="*60)
    
    try:
        visualizer = GraphVisualizer(db)
        
        # Visualize people in tech companies
        print("\n1. Tech company employees:")
        fig = visualizer.plot_query_result(
            "MATCH (p:Person)-[:WORKS_FOR]->(c:Company) WHERE c.industry = 'Technology' RETURN p, c",
            title="Tech Company Network",
            node_color_property='company',
            node_labels=True
        )
        print("✓ Visualized tech company network")
        
        # Visualize management relationships
        print("\n2. Management hierarchy:")
        fig = visualizer.plot_query_result(
            "MATCH (manager:Person)-[:MANAGES]->(employee:Person) RETURN manager, employee",
            title="Management Relationships",
            node_color_property='role',
            node_size_property='salary',
            node_labels=True,
            layout='hierarchical'
        )
        print("✓ Visualized management hierarchy")
        
        # Visualize social connections
        print("\n3. Social network:")
        fig = visualizer.plot_query_result(
            "MATCH (a:Person)-[r:FRIENDS|KNOWS|COLLABORATES]->(b:Person) RETURN a, r, b",
            title="Social Connections",
            node_color_property='location',
            edge_width_property='strength',
            node_labels=True,
            edge_labels=True
        )
        print("✓ Visualized social network")
        
    except Exception as e:
        print(f"⚠️  Query visualization failed: {e}")


def demonstrate_path_visualization(db, person_ids):
    """Demonstrate path visualization."""
    print("\n" + "="*60)
    print("PATH VISUALIZATION")
    print("="*60)
    
    try:
        visualizer = GraphVisualizer(db)
        
        # Find and visualize paths between specific people
        alice_id = person_ids['Alice']
        frank_id = person_ids['Frank']
        
        print(f"\n1. Paths from Alice (ID: {alice_id}) to Frank (ID: {frank_id}):")
        fig = visualizer.plot_path(
            start_node_id=alice_id,
            end_node_id=frank_id,
            max_hops=4,
            title="Paths: Alice → Frank",
            node_labels=True,
            edge_labels=True,
            layout='spring'
        )
        print("✓ Visualized paths between Alice and Frank")
        
        # Visualize variable-length paths
        print("\n2. Variable-length relationship paths:")
        fig = visualizer.plot_query_result(
            f"MATCH path = (alice:Person)-[*1..3]->(others:Person) "
            f"WHERE alice.name = 'Alice' RETURN path",
            title="Alice's Network (1-3 hops)",
            node_color_property='company',
            node_labels=True,
            layout='spring'
        )
        print("✓ Visualized variable-length paths from Alice")
        
    except Exception as e:
        print(f"⚠️  Path visualization failed: {e}")


def demonstrate_interactive_features(db):
    """Demonstrate interactive visualization features."""
    print("\n" + "="*60)
    print("INTERACTIVE VISUALIZATION")
    print("="*60)
    
    try:
        # Create interactive plot with Plotly
        print("\n1. Interactive Plotly visualization:")
        fig = db.visualize(
            backend='plotly',
            title="Interactive Network Explorer",
            node_size_property='salary',
            node_color_property='age',
            node_labels=True,
            layout='spring'
        )
        
        # If we have plotly, we can show additional features
        if fig:
            print("✓ Created interactive visualization")
            print("  Features:")
            print("  - Hover over nodes to see details")
            print("  - Drag to pan, scroll to zoom")
            print("  - Click and drag nodes to rearrange")
            
            # Save as HTML for viewing
            try:
                fig.write_html("interactive_graph.html")
                print("  - Saved as 'interactive_graph.html'")
            except:
                pass
        
    except Exception as e:
        print(f"⚠️  Interactive visualization failed: {e}")


def demonstrate_export_options(db):
    """Demonstrate export and saving options."""
    print("\n" + "="*60)
    print("EXPORT AND SAVING OPTIONS")
    print("="*60)
    
    try:
        # Save static plots
        print("\n1. Saving static plots:")
        fig = db.visualize(
            title="Network for Export",
            node_labels=True,
            node_color_property='company',
            layout='spring',
            save_path='network_plot.png'
        )
        print("✓ Saved static plot as 'network_plot.png'")
        
        # Save interactive plot
        print("\n2. Saving interactive plots:")
        fig = db.visualize(
            backend='plotly',
            title="Interactive Network",
            node_labels=True,
            save_path='interactive_network.html'
        )
        print("✓ Saved interactive plot as 'interactive_network.html'")
        
        # Save high-quality vector graphics
        print("\n3. High-quality vector graphics:")
        visualizer = GraphVisualizer(db)
        if 'graphviz' in visualizer.available_backends:
            fig = visualizer.plot(
                backend='graphviz',
                title="High Quality Network",
                node_labels=True,
                edge_labels=True,
                save_path='network_hq.svg'
            )
            print("✓ Saved high-quality plot as 'network_hq.svg'")
        else:
            print("⚠️  Graphviz not available for vector graphics")
        
    except Exception as e:
        print(f"⚠️  Export failed: {e}")


def demonstrate_performance_with_larger_graph(db):
    """Demonstrate visualization performance with a larger graph."""
    print("\n" + "="*60)
    print("PERFORMANCE WITH LARGER GRAPHS")
    print("="*60)
    
    try:
        import time
        
        # Create additional nodes for performance testing
        print("\n1. Creating larger graph...")
        start_nodes = db.node_count
        
        # Add more nodes
        for i in range(50):
            db.create_node(['TestNode'], {
                'id': f'test_{i}',
                'value': i,
                'category': f'group_{i % 5}'
            })
        
        # Add random relationships
        import random
        all_nodes = db.find_nodes()
        node_ids = [n['id'] for n in all_nodes]
        
        for i in range(100):
            source = random.choice(node_ids)
            target = random.choice(node_ids)
            if source != target:
                db.create_relationship(source, target, 'CONNECTS', {'weight': random.randint(1, 10)})
        
        print(f"Extended graph to {db.node_count} nodes and {db.relationship_count} relationships")
        
        # Test visualization performance
        print("\n2. Testing visualization performance...")
        start_time = time.time()
        fig = db.visualize(
            title=f"Large Graph ({db.node_count} nodes)",
            node_color_property='category',
            layout='spring',
            node_labels=False  # Disable labels for performance
        )
        end_time = time.time()
        
        print(f"✓ Visualized large graph in {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"⚠️  Performance test failed: {e}")


def main():
    """Main demonstration function."""
    print("Graph Visualization Demonstration")
    print("=" * 60)
    print("This example demonstrates comprehensive graph visualization capabilities")
    print("including multiple backends, layouts, styling options, and interactive features.")
    print()
    
    # Check dependencies
    try:
        from contextgraph.visualization import GraphVisualizer
        visualizer_test = GraphVisualizer(None)
        if not visualizer_test.available_backends:
            print("⚠️  No visualization backends available!")
            print("Install dependencies with:")
            install_dependencies()
            return
        else:
            print(f"✓ Available backends: {visualizer_test.available_backends}")
    except Exception as e:
        print(f"⚠️  Visualization module error: {e}")
        return
    
    # Create database and sample data
    db = GraphDB()
    person_ids, company_ids = create_sample_network(db)
    
    # Run demonstrations
    demonstrate_basic_visualization(db)
    demonstrate_different_backends(db)
    demonstrate_different_layouts(db)
    demonstrate_advanced_styling(db)
    demonstrate_query_visualization(db)
    demonstrate_path_visualization(db, person_ids)
    demonstrate_interactive_features(db)
    demonstrate_export_options(db)
    demonstrate_performance_with_larger_graph(db)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("Graph visualization provides powerful capabilities for:")
    print("✓ Exploring graph structure and relationships")
    print("✓ Debugging queries and understanding data")
    print("✓ Creating publication-quality figures")
    print("✓ Interactive data exploration")
    print("✓ Analyzing network patterns and communities")
    print()
    print("Key features demonstrated:")
    print("• Multiple backends: matplotlib, plotly, graphviz")
    print("• Various layouts: spring, circular, hierarchical, etc.")
    print("• Property-based styling: size, color, width")
    print("• Query result visualization")
    print("• Path and subgraph visualization")
    print("• Interactive exploration with hover details")
    print("• Export to multiple formats (PNG, SVG, HTML)")
    print("• Performance optimization for larger graphs")
    print()
    print("For installation help, run: install_dependencies()")


if __name__ == '__main__':
    main()
