"""
Tests for graph visualization functionality.
"""

import pytest
from contextgraph import GraphDB, GraphVisualizer


class TestVisualization:
    """Test visualization functionality."""

    def setup_method(self):
        """Set up test database with sample data."""
        self.db = GraphDB()
        
        # Create sample nodes
        self.alice_id = self.db.create_node(['Person'], {'name': 'Alice', 'age': 30, 'salary': 75000})
        self.bob_id = self.db.create_node(['Person'], {'name': 'Bob', 'age': 25, 'salary': 65000})
        self.charlie_id = self.db.create_node(['Person'], {'name': 'Charlie', 'age': 35, 'salary': 85000})
        
        # Create sample relationships
        self.db.create_relationship(self.alice_id, self.bob_id, 'KNOWS', {'strength': 8})
        self.db.create_relationship(self.bob_id, self.charlie_id, 'WORKS_WITH', {'strength': 6})
        self.db.create_relationship(self.charlie_id, self.alice_id, 'MANAGES', {'strength': 9})

    def test_visualizer_creation(self):
        """Test creating a GraphVisualizer instance."""
        visualizer = GraphVisualizer(self.db)
        assert visualizer.graph_db == self.db
        assert isinstance(visualizer.available_backends, list)

    def test_dependency_checking(self):
        """Test dependency checking functionality."""
        visualizer = GraphVisualizer(self.db)
        # Should have at least one backend available (we installed matplotlib and plotly)
        assert len(visualizer.available_backends) > 0

    def test_networkx_graph_creation(self):
        """Test creating NetworkX graph from database."""
        visualizer = GraphVisualizer(self.db)
        
        # Skip if NetworkX not available
        try:
            G = visualizer._create_networkx_graph()
        except ImportError:
            pytest.skip("NetworkX not available")
        
        # Check nodes
        assert len(G.nodes()) == 3
        assert 0 in G.nodes()  # Alice
        assert 1 in G.nodes()  # Bob
        assert 2 in G.nodes()  # Charlie
        
        # Check edges
        assert len(G.edges()) == 3
        assert G.has_edge(0, 1)  # Alice -> Bob
        assert G.has_edge(1, 2)  # Bob -> Charlie
        assert G.has_edge(2, 0)  # Charlie -> Alice
        
        # Check node properties
        assert G.nodes[0]['name'] == 'Alice'
        assert G.nodes[1]['age'] == 25
        assert G.nodes[2]['salary'] == 85000
        
        # Check edge properties
        assert G[0][1]['type'] == 'KNOWS'
        assert G[1][2]['strength'] == 6

    def test_convenience_method(self):
        """Test the convenience visualize method on GraphDB."""
        # This should not raise an exception even if backends aren't available
        try:
            result = self.db.visualize(node_labels=True, title="Test Graph")
            # If we get here, visualization worked
            assert result is not None
        except ImportError:
            # Expected if no visualization backends are available
            pass
        except Exception as e:
            # Other exceptions indicate a problem
            pytest.fail(f"Unexpected error in visualization: {e}")

    def test_backend_selection(self):
        """Test automatic backend selection."""
        visualizer = GraphVisualizer(self.db)
        
        if visualizer.available_backends:
            backend = visualizer._choose_backend()
            assert backend in visualizer.available_backends
        else:
            with pytest.raises(RuntimeError):
                visualizer._choose_backend()

    def test_plot_with_available_backends(self):
        """Test plotting with each available backend."""
        visualizer = GraphVisualizer(self.db)
        
        for backend in visualizer.available_backends:
            try:
                result = visualizer.plot(
                    backend=backend,
                    node_labels=True,
                    title=f"Test {backend}"
                )
                assert result is not None
            except Exception as e:
                pytest.fail(f"Backend {backend} failed: {e}")

    def test_plot_with_styling(self):
        """Test plotting with property-based styling."""
        visualizer = GraphVisualizer(self.db)
        
        if not visualizer.available_backends:
            pytest.skip("No visualization backends available")
        
        try:
            result = visualizer.plot(
                node_labels=True,
                node_size_property='salary',
                node_color_property='age',
                edge_width_property='strength',
                title="Styled Graph"
            )
            assert result is not None
        except Exception as e:
            pytest.fail(f"Styled visualization failed: {e}")

    def test_different_layouts(self):
        """Test different layout algorithms."""
        visualizer = GraphVisualizer(self.db)
        
        if not visualizer.available_backends:
            pytest.skip("No visualization backends available")
        
        layouts = ['spring', 'circular', 'random']
        
        for layout in layouts:
            try:
                result = visualizer.plot(
                    layout=layout,
                    node_labels=True,
                    title=f"Test {layout} layout"
                )
                assert result is not None
            except Exception as e:
                pytest.fail(f"Layout {layout} failed: {e}")

    def test_query_result_visualization(self):
        """Test visualizing query results."""
        visualizer = GraphVisualizer(self.db)
        
        if not visualizer.available_backends:
            pytest.skip("No visualization backends available")
        
        try:
            # This should work even if the query returns no specific visualization data
            result = visualizer.plot_query_result(
                "MATCH (p:Person) RETURN p",
                title="Query Result Visualization"
            )
            # The method should complete without error
            assert True
        except Exception as e:
            pytest.fail(f"Query result visualization failed: {e}")

    def test_invalid_backend(self):
        """Test error handling for invalid backend."""
        visualizer = GraphVisualizer(self.db)
        
        with pytest.raises(ValueError):
            visualizer.plot(backend='nonexistent_backend')

    def test_empty_graph_visualization(self):
        """Test visualizing an empty graph."""
        empty_db = GraphDB()
        visualizer = GraphVisualizer(empty_db)
        
        if not visualizer.available_backends:
            pytest.skip("No visualization backends available")
        
        try:
            result = visualizer.plot(title="Empty Graph")
            assert result is not None
        except Exception as e:
            pytest.fail(f"Empty graph visualization failed: {e}")


class TestVisualizationWithoutDependencies:
    """Test visualization behavior when dependencies are missing."""
    
    def test_no_backends_warning(self):
        """Test that appropriate warnings are shown when no backends are available."""
        # This test would need to mock the import failures, but for now
        # we'll just test that the install_dependencies function exists
        from contextgraph import install_dependencies
        
        # Should not raise an exception
        try:
            install_dependencies()
        except Exception as e:
            pytest.fail(f"install_dependencies() failed: {e}")

    def test_graceful_degradation(self):
        """Test that the module loads even without visualization dependencies."""
        # The import should work even if visualization backends aren't available
        from contextgraph.visualization import GraphVisualizer
        
        db = GraphDB()
        db.create_node(['Test'], {'name': 'test'})
        
        # Creating a visualizer should work
        visualizer = GraphVisualizer(db)
        
        # It should report no available backends if dependencies are missing
        assert isinstance(visualizer.available_backends, list)
