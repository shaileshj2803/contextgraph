"""
Cypher query parser and executor using pyparsing.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from pyparsing import (
    Word, Literal, CaselessKeyword, alphas, alphanums,
    QuotedString, Suppress, Group, Optional as Opt, ZeroOrMore, OneOrMore,
    delimitedList, pyparsing_common, ParseException, ParserElement,
    Forward, infixNotation, opAssoc
)
import re

from .exceptions import CypherSyntaxError, GraphDBError
from .query_result import QueryResult

# Enable packrat parsing for better performance
ParserElement.enablePackrat()

class CypherParser:
    """
    Cypher query parser and executor.

    This class parses Cypher queries using pyparsing and executes them
    against the graph database.
    """

    def __init__(self, graph_db):
        """
        Initialize the Cypher parser.

        Args:
            graph_db: The GraphDB instance to execute queries against
        """
        self.graph_db = graph_db
        self._setup_grammar()

    def _setup_grammar(self):
        """Set up the pyparsing grammar for Cypher queries."""

        # Basic tokens
        identifier = Word(alphas + "_", alphanums + "_")
        integer = pyparsing_common.signed_integer()
        real = pyparsing_common.real()
        string_literal = (QuotedString("'", escChar="\\") |
                          QuotedString('"', escChar="\\"))

        # Keywords (case - insensitive)
        CREATE = CaselessKeyword("CREATE")
        MATCH = CaselessKeyword("MATCH")
        WHERE = CaselessKeyword("WHERE")
        RETURN = CaselessKeyword("RETURN")
        DELETE = CaselessKeyword("DELETE")
        SET = CaselessKeyword("SET")
        ORDER = CaselessKeyword("ORDER")
        BY = CaselessKeyword("BY")
        LIMIT = CaselessKeyword("LIMIT")
        SKIP = CaselessKeyword("SKIP")
        ASC = CaselessKeyword("ASC")
        DESC = CaselessKeyword("DESC")
        AND = CaselessKeyword("AND")
        OR = CaselessKeyword("OR")
        NOT = CaselessKeyword("NOT")
        NULL = CaselessKeyword("NULL")
        TRUE = CaselessKeyword("TRUE")
        FALSE = CaselessKeyword("FALSE")
        AS = CaselessKeyword("AS")
        DISTINCT = CaselessKeyword("DISTINCT")
        COUNT = CaselessKeyword("COUNT")
        SUM = CaselessKeyword("SUM")
        AVG = CaselessKeyword("AVG")
        MIN = CaselessKeyword("MIN")
        MAX = CaselessKeyword("MAX")

        # String functions
        UPPER = CaselessKeyword("UPPER")
        LOWER = CaselessKeyword("LOWER")
        TRIM = CaselessKeyword("TRIM")
        LTRIM = CaselessKeyword("LTRIM")
        RTRIM = CaselessKeyword("RTRIM")
        LENGTH = CaselessKeyword("LENGTH")
        SUBSTRING = CaselessKeyword("SUBSTRING")
        REPLACE = CaselessKeyword("REPLACE")
        SPLIT = CaselessKeyword("SPLIT")
        REVERSE = CaselessKeyword("REVERSE")

        # Values
        null_value = NULL
        boolean_value = TRUE | FALSE
        number_value = real | integer
        value = (null_value | boolean_value | number_value | string_literal)

        # Property map
        property_key = identifier
        property_value = value
        property_pair = Group(property_key + Suppress(":") + property_value)
        property_map = (Suppress("{") +
                        Opt(delimitedList(property_pair)) +
                        Suppress("}"))

        # Labels
        label = Suppress(":") + identifier
        labels = OneOrMore(label)

        # Variables and expressions
        variable = identifier

        # Property access
        property_access = Group(variable + Suppress(".") + identifier)

        # Forward declarations
        expression = Forward()

        # Function calls
        aggregate_function = (COUNT | SUM | AVG | MIN | MAX)
        string_function = (UPPER | LOWER | TRIM | LTRIM | RTRIM | LENGTH | REVERSE)
        multi_arg_function = (SUBSTRING | REPLACE | SPLIT)

        # Single argument functions
        single_arg_function_call = Group(
            (aggregate_function | string_function) +
            Suppress("(") +
            (Literal("*") | expression) +
            Suppress(")")
        )

        # Multi - argument functions (SUBSTRING, REPLACE, etc.)
        multi_arg_function_call = Group(
            multi_arg_function +
            Suppress("(") +
            delimitedList(expression) +
            Suppress(")")
        )

        function_call = single_arg_function_call | multi_arg_function_call

        # String search operators (must come before comparison operators)
        starts_with = Group(CaselessKeyword("STARTS") + CaselessKeyword("WITH"))
        ends_with = Group(CaselessKeyword("ENDS") + CaselessKeyword("WITH"))
        string_op = (Literal("=~") |  # Regex operator (must come first)
                     CaselessKeyword("CONTAINS") |
                     starts_with |
                     ends_with)

        # Comparison operators (order matters - longer operators first)
        comparison_op = (Literal("<=") | Literal(">=") | Literal("<>") |
                         Literal("!=") | Literal("=") | Literal("<") |
                         Literal(">"))

        # Basic expressions
        atom = (function_call | property_access | variable | value)

        # Comparison expression (try string operators first)
        comparison = Group(atom + (string_op | comparison_op) + atom)

        # Logical expressions
        logical_expr = infixNotation(
            comparison | atom,
            [
                (NOT, 1, opAssoc.RIGHT),
                (AND, 2, opAssoc.LEFT),
                (OR, 2, opAssoc.LEFT),
            ]
        )

        expression <<= logical_expr

        # Node patterns
        node_variable = Opt(variable)
        node_labels = Opt(labels)
        node_properties = Opt(property_map)
        node_pattern = (Suppress("(") +
                        Group(node_variable + node_labels + node_properties) +
                        Suppress(")"))

        # Relationship patterns
        rel_variable = Opt(variable)
        rel_type = Opt(Suppress(":") + identifier)
        rel_properties = Opt(property_map)
        
        # Variable-length path syntax: *min..max, *n, or *
        var_length_exact = Suppress("*") + integer  # *2
        var_length_range = Suppress("*") + integer + Suppress("..") + integer  # *1..3
        var_length_unlimited = Literal("*")  # * (keep the * to distinguish from regular relationships)
        var_length = Opt(var_length_range | var_length_exact | var_length_unlimited)
        
        rel_detail = Group(rel_variable + rel_type + var_length + rel_properties)

        # Relationship directions
        left_arrow = Suppress("<-")
        right_arrow = Suppress("->")
        undirected = Suppress("-")

        relationship_pattern = Group(
            (left_arrow + Suppress("[") + rel_detail + Suppress("]") +
             undirected) |
            (undirected + Suppress("[") + rel_detail + Suppress("]") +
             right_arrow) |
            (undirected + Suppress("[") + rel_detail + Suppress("]") +
             undirected) |
            (left_arrow + undirected) |
            (undirected + right_arrow) |
            undirected
        )

        # Path patterns
        path_pattern = (node_pattern +
                        ZeroOrMore(relationship_pattern + node_pattern))

        # Pattern
        pattern = Group(path_pattern)
        pattern_list = delimitedList(pattern)

        # WHERE clause
        where_clause = WHERE + expression

        # RETURN clause
        return_item = Group((function_call | property_access | variable) +
                            Opt(AS + identifier))
        return_list = delimitedList(return_item)
        return_clause = RETURN + Opt(DISTINCT) + return_list

        # ORDER BY clause
        order_item = Group((property_access | variable) + Opt(ASC | DESC))
        order_list = delimitedList(order_item)
        order_clause = ORDER + BY + order_list

        # LIMIT and SKIP
        limit_clause = LIMIT + integer
        skip_clause = SKIP + integer

        # SET clause
        set_item = Group((property_access | variable) + Suppress("=") + value)
        set_list = delimitedList(set_item)
        set_clause = SET + set_list

        # DELETE clause
        delete_list = delimitedList(variable)
        delete_clause = DELETE + delete_list

        # Main query clauses
        create_clause = CREATE + pattern_list
        match_clause = MATCH + pattern_list

        # Complete query
        query = (
            Opt(match_clause)("match") +
            Opt(where_clause)("where") +
            Opt(create_clause)("create") +
            Opt(set_clause)("set") +
            Opt(delete_clause)("delete") +
            Opt(return_clause)("return") +
            Opt(order_clause)("order") +
            Opt(skip_clause)("skip") +
            Opt(limit_clause)("limit")
        )

        self.grammar = query

    def parse_and_execute(self, cypher_query: str,
                          parameters: Dict[str, Any] = None) -> QueryResult:
        """
        Parse and execute a Cypher query.

        Args:
            cypher_query: The Cypher query string
            parameters: Optional parameters for the query

        Returns:
            QueryResult containing the query results

        Raises:
            CypherSyntaxError: If the query has syntax errors
            GraphDBError: If there's an error during query execution
        """
        if parameters is None:
            parameters = {}

        try:
            # Parse the query
            parsed = self.grammar.parseString(cypher_query, parseAll=True)

            # Execute the parsed query
            return self._execute_parsed_query(parsed, parameters)

        except ParseException as e:
            raise CypherSyntaxError(
                f"Syntax error in Cypher query at position {e.loc}: {e.msg}")
        except Exception as e:
            raise GraphDBError(f"Error executing Cypher query: {str(e)}")

    def _execute_parsed_query(self, parsed_query,
                              parameters: Dict[str, Any]) -> QueryResult:
        """Execute a parsed Cypher query."""

        # Initialize execution context
        context = {
            'variables': {},
            'variable_bindings': [],  # List of variable binding combinations
            'parameters': parameters
        }

        results = []
        columns = []

        # Execute clauses in order
        if 'match' in parsed_query:
            self._execute_match(parsed_query['match'], context)

        if 'create' in parsed_query:
            self._execute_create(parsed_query['create'], context)

        if 'where' in parsed_query:
            self._execute_where(parsed_query['where'], context)

        if 'set' in parsed_query:
            self._execute_set(parsed_query['set'], context)

        if 'delete' in parsed_query:
            self._execute_delete(parsed_query['delete'], context)

        if 'return' in parsed_query:
            results, columns = self._execute_return(parsed_query['return'],
                                                    context)

        # Apply ordering, skip, and limit
        if 'order' in parsed_query:
            results = self._apply_ordering(results, columns,
                                          parsed_query['order'])

        if 'skip' in parsed_query:
            skip_count = parsed_query['skip'][1]  # Skip the SKIP keyword
            results = results[skip_count:]

        if 'limit' in parsed_query:
            limit_count = parsed_query['limit'][1]  # Skip the LIMIT keyword
            results = results[:limit_count]

        return QueryResult(columns, results)

    def _execute_match(self, match_clause, context):
        """Execute a MATCH clause."""
        patterns = match_clause[1:]  # Skip the MATCH keyword

        # Initialize variable bindings if empty
        if not context['variable_bindings']:
            context['variable_bindings'] = [{}]

        for pattern in patterns:
            self._match_pattern(pattern, context)

    def _execute_create(self, create_clause, context):
        """Execute a CREATE clause."""
        patterns = create_clause[1:]  # Skip the CREATE keyword

        # If no variable bindings exist, create one empty binding
        if not context['variable_bindings']:
            context['variable_bindings'] = [{}]

        for pattern in patterns:
            self._create_pattern(pattern, context)

    def _execute_where(self, where_clause, context):
        """Execute a WHERE clause."""
        condition = where_clause[1]  # Skip the WHERE keyword

        # Filter variable bindings based on condition
        filtered_bindings = []
        for binding in context['variable_bindings']:
            if self._evaluate_condition(condition, binding, context):
                filtered_bindings.append(binding)

        context['variable_bindings'] = filtered_bindings

    def _execute_set(self, set_clause, context):
        """Execute a SET clause."""
        assignments = set_clause[1:]  # Skip the SET keyword

        for binding in context['variable_bindings']:
            for assignment in assignments:
                self._execute_assignment(assignment, binding, context)

    def _execute_delete(self, delete_clause, context):
        """Execute a DELETE clause."""
        variables = delete_clause[1:]  # Skip the DELETE keyword

        for binding in context['variable_bindings']:
            for var_name in variables:
                if var_name in binding:
                    var_value = binding[var_name]
                    if isinstance(var_value, dict) and 'id' in var_value:
                        # Delete node or relationship
                        if 'labels' in var_value:  # It's a node
                            self.graph_db.delete_node(var_value['id'])
                        else:  # It's a relationship
                            self.graph_db.delete_relationship(var_value['id'])

    def _execute_return(self, return_clause, context):
        """Execute a RETURN clause."""
        return_items = return_clause[1:]  # Skip the RETURN keyword

        # Handle DISTINCT
        distinct = False
        if return_items and str(return_items[0]).upper() == 'DISTINCT':
            distinct = True
            return_items = return_items[1:]

        columns = []
        results = []

        # Extract column names - each item is a separate list
        for item in return_items:
            if hasattr(item, '__len__') and len(item) >= 1:
                # Item is like [['n', 'name']] or ['COUNT', '*'] or [['TRIM', ['t', 'padded']], 'AS', 'trimmed']
                if hasattr(item[0], '__len__'):
                    expr = item[0]  # The actual expression
                else:
                    expr = item

                # Check for alias: item structure is [expression, 'AS', alias_name]
                alias = None
                if len(item) >= 3 and str(item[1]).upper() == 'AS':
                    alias = str(item[2])
                elif len(item) == 2 and str(item[1]).upper() != 'AS':
                    # Direct alias without AS keyword (shouldn't happen with current grammar)
                    alias = str(item[1])

                if alias:
                    columns.append(alias)
                else:
                    columns.append(self._expression_to_string(expr))

        # Check if we have aggregate functions
        has_aggregates = False
        for item in return_items:
            if hasattr(item, '__len__') and len(item) >= 1:
                # Item structure is like [['COUNT', '*']] or [['p', 'name']]
                if hasattr(item[0], '__len__') and len(item[0]) >= 1:
                    expr = item[0]  # This is ['COUNT', '*'] or ['p', 'name']
                    if str(expr[0]).upper() in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']:
                        has_aggregates = True
                        break

        # Generate result rows
        if has_aggregates:
            # For aggregate functions, return a single row
            row = []
            for item in return_items:
                if hasattr(item, '__len__') and len(item) >= 1:
                    if hasattr(item[0], '__len__'):
                        expr = item[0]
                    else:
                        expr = item

                    # For aggregates, we need to pass a dummy binding but the context has all bindings
                    value = self._evaluate_expression(expr, {}, context)
                    row.append(value)
            if row:
                results.append(row)
        elif context['variable_bindings']:
            # Regular non - aggregate query
            for binding in context['variable_bindings']:
                row = []
                for item in return_items:
                    if hasattr(item, '__len__') and len(item) >= 1:
                        if hasattr(item[0], '__len__'):
                            expr = item[0]
                        else:
                            expr = item

                        value = self._evaluate_expression(expr, binding, context)
                        row.append(value)
                results.append(row)
        else:
            # No variable bindings and no aggregates
            pass

        if distinct:
            # Remove duplicates
            seen = set()
            unique_results = []
            for row in results:
                row_tuple = tuple(str(x) for x in row)  # Convert to strings for hashing
                if row_tuple not in seen:
                    seen.add(row_tuple)
                    unique_results.append(row)
            results = unique_results

        return results, columns

    def _match_pattern(self, pattern, context):
        """Match a pattern against the graph."""
        elements = pattern

        # Parse the pattern into nodes and relationships
        nodes = []
        relationships = []

        i = 0
        while i < len(elements):
            element = elements[i]
            if self._is_node_pattern(element):
                nodes.append(element)
            elif self._is_relationship_pattern(element):
                relationships.append(element)
            i += 1

        # If we have relationships, we need to do a more complex matching
        if relationships:
            self._match_path_pattern(nodes, relationships, context)
        else:
            # Simple node matching without relationships
            new_bindings = []
            for binding in context['variable_bindings']:
                node_matches = self._match_nodes_in_pattern(nodes, binding)
                if node_matches:
                    new_bindings.extend(node_matches)

            if new_bindings:
                context['variable_bindings'] = new_bindings
            else:
                # No matches found
                context['variable_bindings'] = []

    def _match_nodes_in_pattern(self, nodes, current_binding):
        """Match nodes in a pattern and return possible bindings."""
        if not nodes:
            return [current_binding]

        node_pattern = nodes[0]
        remaining_nodes = nodes[1:]

        # Extract variable
        variable = node_pattern[0] if len(node_pattern) > 0 else None

        # Determine if we have labels or just properties
        # Labels are strings, properties are lists with 2 elements
        labels = []
        property_pairs = []

        for i in range(1, len(node_pattern)):
            element = node_pattern[i]
            if isinstance(element, str):
                # It's a label
                labels.append(element)
            elif hasattr(element, '__len__') and len(element) == 2:
                # It's a property pair
                property_pairs.append(element)

        # Convert properties to dictionary
        prop_dict = {}
        for prop_pair in property_pairs:
            key = str(prop_pair[0])
            value = self._convert_value(prop_pair[1])
            prop_dict[key] = value

        # Find matching nodes
        matching_nodes = self.graph_db.find_nodes(labels if labels else None,
                                                 prop_dict if prop_dict else None)

        bindings = []
        for node in matching_nodes:
            new_binding = current_binding.copy()
            if variable:
                new_binding[str(variable)] = node

            # Recursively match remaining nodes
            if remaining_nodes:
                sub_bindings = self._match_nodes_in_pattern(remaining_nodes, new_binding)
                bindings.extend(sub_bindings)
            else:
                bindings.append(new_binding)

        return bindings

    def _match_relationships_in_pattern(self, relationships, nodes, context):
        """Match relationships in a pattern."""
        if not relationships or not nodes or len(nodes) < 2:
            return

        # For each relationship, we need to match it between consecutive nodes
        filtered_bindings = []

        for binding in context['variable_bindings']:
            if self._validate_relationship_pattern(relationships, nodes, binding):
                filtered_bindings.append(binding)

        context['variable_bindings'] = filtered_bindings

    def _match_path_pattern(self, nodes, relationships, context):
        """Match a path pattern with nodes and relationships."""
        if len(nodes) != len(relationships) + 1:
            # Invalid pattern structure
            context['variable_bindings'] = []
            return

        # Start fresh - find all valid paths from scratch
        new_bindings = []

        # Get all nodes that match the first pattern
        first_node_matches = self._find_all_matching_nodes(nodes[0])

        # For each matching first node, try to find valid paths
        for start_node in first_node_matches:
            start_binding = {}
            first_var = nodes[0][0] if len(nodes[0]) > 0 else None
            if first_var:
                start_binding[str(first_var)] = start_node

            path_bindings = self._find_valid_paths(nodes, relationships, start_binding, 0)
            new_bindings.extend(path_bindings)

        context['variable_bindings'] = new_bindings

    def _find_valid_paths(self, nodes, relationships, current_binding, node_index):
        """Recursively find valid paths through the graph."""
        if node_index >= len(nodes) - 1:
            # We've matched all nodes in the path
            return [current_binding]

        current_node_var = nodes[node_index][0] if len(nodes[node_index]) > 0 else None
        next_node_pattern = nodes[node_index + 1]
        relationship_pattern = relationships[node_index]

        if not current_node_var or current_node_var not in current_binding:
            return []

        current_node = current_binding[current_node_var]
        if not isinstance(current_node, dict) or 'id' not in current_node:
            return []

        # Check if this is a variable-length relationship
        var_length = self._parse_variable_length(relationship_pattern)
        
        if var_length:
            # Handle variable-length path
            min_hops, max_hops = var_length
            return self._handle_variable_length_path(
                current_node, relationship_pattern, next_node_pattern,
                min_hops, max_hops, current_binding, nodes, relationships, node_index
            )
        
        # Handle regular single-hop relationship
        valid_paths = []
        all_relationships = self.graph_db.find_relationships()

        for rel in all_relationships:
            if self._relationship_matches_pattern(rel, relationship_pattern, current_node['id']):
                # Find the target node - for now, assume directed relationships (->)
                # Only follow relationships where current node is the source
                if rel['source'] == current_node['id']:
                    target_node_id = rel['target']
                    target_node = self.graph_db.get_node(target_node_id)
                else:
                    continue  # Skip relationships where current node is not the source

                if target_node and self._node_matches_pattern(target_node, next_node_pattern):
                    # Create new binding with the target node
                    new_binding = current_binding.copy()
                    next_node_var = next_node_pattern[0] if len(next_node_pattern) > 0 else None
                    if next_node_var:
                        new_binding[str(next_node_var)] = target_node

                    # Store relationship if it has a variable
                    rel_var = self._get_relationship_variable(relationship_pattern)
                    if rel_var:
                        new_binding[str(rel_var)] = rel

                    # Recursively find the rest of the path
                    sub_paths = self._find_valid_paths(nodes, relationships, new_binding, node_index + 1)
                    valid_paths.extend(sub_paths)

        return valid_paths

    def _match_single_node_pattern(self, node_pattern, current_binding):
        """Match a single node pattern and return possible bindings."""
        return self._match_nodes_in_pattern([node_pattern], current_binding)

    def _find_all_matching_nodes(self, node_pattern):
        """Find all nodes in the graph that match the given pattern."""
        # Extract labels and properties from pattern
        labels = []
        property_pairs = []

        for i in range(1, len(node_pattern)):
            element = node_pattern[i]
            if isinstance(element, str):
                labels.append(element)
            elif hasattr(element, '__len__') and len(element) == 2:
                property_pairs.append(element)

        # Convert properties to dictionary
        prop_dict = {}
        for prop_pair in property_pairs:
            key = str(prop_pair[0])
            value = self._convert_value(prop_pair[1])
            prop_dict[key] = value

        # Find matching nodes
        return self.graph_db.find_nodes(labels=labels if labels else None, properties=prop_dict if prop_dict else None)

    def _relationship_matches_pattern(self, relationship, pattern, source_node_id):
        """Check if a relationship matches the given pattern."""
        # Extract relationship type from pattern
        rel_type = None

        if hasattr(pattern, '__len__') and len(pattern) > 0:
            rel_detail = pattern[0]  # This is ['WORKS_FOR'] or similar
            if hasattr(rel_detail, '__len__') and len(rel_detail) > 0:
                rel_type = str(rel_detail[0])

        # Check if relationship type matches
        if rel_type and relationship['type'] != rel_type:
            return False

        # Check if the relationship connects from the source node (directed)
        if relationship['source'] != source_node_id:
            return False

        return True

    def _node_matches_pattern(self, node, pattern):
        """Check if a node matches the given pattern."""
        # Extract labels and properties from pattern
        labels = []
        property_pairs = []

        for i in range(1, len(pattern)):
            element = pattern[i]
            if isinstance(element, str):
                labels.append(element)
            elif hasattr(element, '__len__') and len(element) == 2:
                property_pairs.append(element)

        # Check labels
        if labels:
            node_labels = node.get('labels', [])
            if not all(label in node_labels for label in labels):
                return False

        # Check properties
        if property_pairs:
            node_props = node.get('properties', {})
            for prop_pair in property_pairs:
                key = str(prop_pair[0])
                value = self._convert_value(prop_pair[1])
                if node_props.get(key) != value:
                    return False

        return True

    def _get_relationship_variable(self, pattern):
        """Extract relationship variable from pattern if present."""
        # For now, relationships don't have variables in our simple patterns
        # This would be extended for patterns like (a)-[r:KNOWS]->(b)
        return None

    def _validate_relationship_pattern(self, relationships, nodes, binding):
        """Validate that relationships exist between bound nodes."""
        # This is a simplified version - the main logic is now in _match_path_pattern
        return True

    def _create_pattern(self, pattern, context):
        """Create a pattern in the graph."""
        if not hasattr(pattern, '__len__') or len(pattern) == 0:
            return

        # Parse the pattern into nodes and relationships
        nodes = []
        relationships = []

        for element in pattern:
            if self._is_node_pattern(element):
                nodes.append(element)
            elif self._is_relationship_pattern(element):
                relationships.append(element)

        # If we have relationships, create a path pattern
        if relationships:
            self._create_path_pattern(nodes, relationships, context)
        else:
            # Simple node creation without relationships
            if context['variable_bindings']:
                for binding in context['variable_bindings']:
                    for node_pattern in nodes:
                        self._create_node_pattern(node_pattern, binding)
            else:
                # No existing bindings, create a new one
                binding = {}
                context['variable_bindings'] = [binding]
                for node_pattern in nodes:
                    self._create_node_pattern(node_pattern, binding)

    def _create_node_pattern(self, node_pattern, binding):
        """Create a node from a pattern."""
        # Extract variable
        variable = node_pattern[0] if len(node_pattern) > 0 else None

        # Determine if we have labels or just properties
        # Labels are strings, properties are lists with 2 elements
        labels = []
        property_pairs = []

        for i in range(1, len(node_pattern)):
            element = node_pattern[i]
            if isinstance(element, str):
                # It's a label
                labels.append(element)
            elif hasattr(element, '__len__') and len(element) == 2:
                # It's a property pair
                property_pairs.append(element)

        # Convert properties to dictionary
        prop_dict = {}
        for prop_pair in property_pairs:
            key = str(prop_pair[0])
            value = self._convert_value(prop_pair[1])
            prop_dict[key] = value

        # Create the node
        node_id = self.graph_db.create_node(labels, prop_dict)

        # Store in binding if variable is specified
        if variable:
            node_data = self.graph_db.get_node(node_id)
            binding[str(variable)] = node_data

        return node_id

    def _create_path_pattern(self, nodes, relationships, context):
        """Create a path pattern with nodes and relationships."""
        if len(nodes) != len(relationships) + 1:
            raise CypherSyntaxError(f"Invalid path pattern: {len(nodes)} nodes, {len(relationships)} relationships")

        # If no existing bindings, create one
        if not context['variable_bindings']:
            context['variable_bindings'] = [{}]

        # For each binding, create the path
        for binding in context['variable_bindings']:
            self._create_single_path(nodes, relationships, binding)

    def _create_single_path(self, nodes, relationships, binding):
        """Create a single path with nodes and relationships."""
        created_nodes = []

        # Create or get all nodes first
        for node_pattern in nodes:
            variable = node_pattern[0] if len(node_pattern) > 0 else None

            # Check if node already exists in binding
            if variable and str(variable) in binding:
                # Use existing node
                existing_node = binding[str(variable)]
                if isinstance(existing_node, dict) and 'id' in existing_node:
                    created_nodes.append(existing_node['id'])
                else:
                    raise CypherSyntaxError(f"Invalid node reference: {variable}")
            else:
                # Create new node
                node_id = self._create_node_pattern(node_pattern, binding)
                created_nodes.append(node_id)

        # Create relationships between consecutive nodes
        for i, rel_pattern in enumerate(relationships):
            source_id = created_nodes[i]
            target_id = created_nodes[i + 1]

            # Extract relationship type and properties
            rel_type, rel_properties = self._parse_relationship_pattern(rel_pattern)

            # Create the relationship
            rel_id = self.graph_db.create_relationship(source_id, target_id, rel_type, rel_properties)

            # Store relationship in binding if it has a variable
            rel_var = self._get_relationship_variable(rel_pattern)
            if rel_var:
                rel_data = {
                    'id': rel_id,
                    'type': rel_type,
                    'properties': rel_properties,
                    'source': source_id,
                    'target': target_id
                }
                binding[str(rel_var)] = rel_data

    def _parse_relationship_pattern(self, rel_pattern):
        """Parse a relationship pattern to extract type and properties."""
        rel_type = "RELATED"  # Default type
        rel_properties = {}

        if hasattr(rel_pattern, '__len__') and len(rel_pattern) > 0:
            rel_detail = rel_pattern[0]  # This is ['WORKS_FOR'] or similar
            if hasattr(rel_detail, '__len__') and len(rel_detail) > 0:
                rel_type = str(rel_detail[0])

                # TODO: Add support for relationship properties
                # This would handle patterns like [:WORKS_FOR {since: 2020}]

        return rel_type, rel_properties

    def _execute_assignment(self, assignment, binding, context):
        """Execute a SET assignment."""
        target, value = assignment

        if isinstance(target, list) and len(target) == 2:
            # Property assignment: variable.property = value
            var_name, prop_name = target
            if str(var_name) in binding:
                var_value = binding[str(var_name)]
                if isinstance(var_value, dict) and 'id' in var_value:
                    # Update the property in the database
                    # This would require extending the GraphDB API
                    pass

    def _evaluate_condition(self, condition, binding, context):
        """Evaluate a WHERE condition."""
        if isinstance(condition, list):
            if len(condition) == 3:
                # Binary operation
                left, op, right = condition
                left_val = self._evaluate_expression(left, binding, context)
                right_val = self._evaluate_expression(right, binding, context)

                return self._apply_operator(left_val, op, right_val)
            elif len(condition) == 2:
                # Unary operation (like NOT)
                op, operand = condition
                if str(op).upper() == 'NOT':
                    return not self._evaluate_condition(operand, binding, context)

        # Single value condition
        return bool(self._evaluate_expression(condition, binding, context))

    def _evaluate_expression(self, expression, binding, context):
        """Evaluate an expression in the given context."""
        if isinstance(expression, str):
            # It's a variable reference or literal
            if expression in binding:
                return binding[expression]
            elif expression in context['parameters']:
                return context['parameters'][expression]
            else:
                # Try to convert to appropriate type
                return self._convert_value(expression)

        elif isinstance(expression, (int, float, bool)):
            return expression

        elif hasattr(expression, '__len__'):
            if len(expression) == 2:
                # Could be property access or function call
                first_elem = str(expression[0]).upper()
                if first_elem in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE', 'SUBSTRING', 'REPLACE', 'SPLIT']:
                    # Function call
                    return self._evaluate_function(expression, binding, context)
                else:
                    # Property access: [variable, property]
                    var_name, prop_name = expression
                    if str(var_name) in binding:
                        var_value = binding[str(var_name)]
                        if isinstance(var_value, dict) and 'properties' in var_value:
                            return var_value['properties'].get(str(prop_name))
            elif len(expression) >= 3:
                # Function call or binary operation
                if str(expression[0]).upper() in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE', 'SUBSTRING', 'REPLACE', 'SPLIT']:
                    return self._evaluate_function(expression, binding, context)
                elif len(expression) == 3:
                    # Binary operation
                    left, op, right = expression
                    left_val = self._evaluate_expression(left, binding, context)
                    right_val = self._evaluate_expression(right, binding, context)
                    return self._apply_operator(left_val, op, right_val)

        return None

    def _evaluate_function(self, func_expr, binding, context):
        """Evaluate aggregate and string functions."""
        func_name = str(func_expr[0]).upper()

        # String functions (non - aggregate, work on single values)
        if func_name in ['UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE']:
            if len(func_expr) < 2:
                return None
            arg = func_expr[1]
            val = self._evaluate_expression(arg, binding, context)
            return self._evaluate_string_function(func_name, [val])

        # Multi - argument string functions
        elif func_name in ['SUBSTRING', 'REPLACE', 'SPLIT']:
            if len(func_expr) < 2:
                return None
            # For multi-arg functions, arguments start from func_expr[1] onwards
            args = []
            for i in range(1, len(func_expr)):
                val = self._evaluate_expression(func_expr[i], binding, context)
                args.append(val)
            return self._evaluate_string_function(func_name, args)

        # Aggregate functions (work on collections)
        elif func_name in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']:
            if len(func_expr) < 2:
                return None
            arg = func_expr[1]

            if func_name == 'COUNT':
                if str(arg) == '*':
                    return len(context['variable_bindings'])
                else:
                    # Count non - null values
                    count = 0
                    for b in context['variable_bindings']:
                        temp_context = context.copy()
                        val = self._evaluate_expression(arg, b, temp_context)
                        if val is not None:
                            count += 1
                    return count

            # For other aggregate functions, collect all values first
            values = []
            for b in context['variable_bindings']:
                temp_context = context.copy()
                val = self._evaluate_expression(arg, b, temp_context)
                if val is not None and isinstance(val, (int, float)):
                    values.append(val)

            if not values:
                return None

            if func_name == 'SUM':
                return sum(values)
            elif func_name == 'AVG':
                return sum(values) / len(values)
            elif func_name == 'MIN':
                return min(values)
            elif func_name == 'MAX':
                return max(values)

        return None

    def _apply_operator(self, left, op, right):
        """Apply a binary operator."""
        op_str = str(op)

        # Handle None values gracefully
        if left is None or right is None:
            if op_str == '=':
                return left == right  # None == None is True, None == value is False
            elif op_str in ['<>', '!=']:
                return left != right  # None != None is False, None != value is True
            else:
                # For comparison operators, None is always False
                return False

        if op_str == '=':
            return left == right
        elif op_str in ['<>', '!=']:
            return left != right
        elif op_str == '<':
            try:
                return left < right
            except TypeError:
                return False
        elif op_str == '<=':
            try:
                return left <= right
            except TypeError:
                return False
        elif op_str == '>':
            try:
                return left > right
            except TypeError:
                return False
        elif op_str == '>=':
            try:
                return left >= right
            except TypeError:
                return False
        elif op_str.upper() == 'AND':
            return bool(left) and bool(right)
        elif op_str.upper() == 'OR':
            return bool(left) or bool(right)

        # String search operators
        elif op_str.upper() == 'CONTAINS':
            return self._string_contains(left, right)
        elif (op_str.upper() in ['STARTS WITH', 'STARTSWITH'] or
              str(op).upper().replace(' ', '') == 'STARTSWITH' or
              (hasattr(op, '__iter__') and len(op) == 2 and
               str(op[0]).upper() == 'STARTS' and str(op[1]).upper() == 'WITH')):
            return self._string_starts_with(left, right)
        elif (op_str.upper() in ['ENDS WITH', 'ENDSWITH'] or
              str(op).upper().replace(' ', '') == 'ENDSWITH' or
              (hasattr(op, '__iter__') and len(op) == 2 and
               str(op[0]).upper() == 'ENDS' and str(op[1]).upper() == 'WITH')):
            return self._string_ends_with(left, right)
        elif op_str == '=~':
            return self._string_regex_match(left, right)

        return False

    def _string_contains(self, left, right):
        """Check if left string contains right string (case - sensitive)."""
        if left is None or right is None:
            return False

        try:
            left_str = str(left)
            right_str = str(right)
            return right_str in left_str
        except (TypeError, ValueError):
            return False

    def _string_starts_with(self, left, right):
        """Check if left string starts with right string (case - sensitive)."""
        if left is None or right is None:
            return False

        try:
            left_str = str(left)
            right_str = str(right)
            return left_str.startswith(right_str)
        except (TypeError, ValueError):
            return False

    def _string_ends_with(self, left, right):
        """Check if left string ends with right string (case - sensitive)."""
        if left is None or right is None:
            return False

        try:
            left_str = str(left)
            right_str = str(right)
            return left_str.endswith(right_str)
        except (TypeError, ValueError):
            return False

    def _string_regex_match(self, left, right):
        """Check if left string matches right regex pattern."""
        if left is None or right is None:
            return False

        try:
            left_str = str(left)
            pattern = str(right)
            return bool(re.search(pattern, left_str))
        except (TypeError, ValueError, re.error):
            return False

    def _evaluate_string_function(self, func_name, args):
        """Evaluate string manipulation functions."""
        if not args or args[0] is None:
            return None

        try:
            text = str(args[0])

            if func_name == 'UPPER':
                return text.upper()
            elif func_name == 'LOWER':
                return text.lower()
            elif func_name == 'TRIM':
                return text.strip()
            elif func_name == 'LTRIM':
                return text.lstrip()
            elif func_name == 'RTRIM':
                return text.rstrip()
            elif func_name == 'LENGTH':
                return len(text)
            elif func_name == 'REVERSE':
                return text[::-1]
            elif func_name == 'SUBSTRING':
                if len(args) < 2:
                    return None
                try:
                    start = int(args[1])
                    if len(args) >= 3:
                        length = int(args[2])
                        return text[start:start + length]
                    else:
                        return text[start:]
                except (ValueError, IndexError):
                    return None
            elif func_name == 'REPLACE':
                if len(args) < 3:
                    return None
                try:
                    old_str = str(args[1])
                    new_str = str(args[2])
                    return text.replace(old_str, new_str)
                except (TypeError, ValueError):
                    return None
            elif func_name == 'SPLIT':
                if len(args) < 2:
                    return text.split()  # Split on whitespace
                try:
                    delimiter = str(args[1])
                    return text.split(delimiter)
                except (TypeError, ValueError):
                    return None

        except (TypeError, ValueError):
            return None

        return None

    def _convert_value(self, value):
        """Convert a parsed value to appropriate Python type."""
        if isinstance(value, str):
            if value.upper() == 'NULL':
                return None
            elif value.upper() == 'TRUE':
                return True
            elif value.upper() == 'FALSE':
                return False
            else:
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    return value[1:-1]
                return value
        return value

    def _is_node_pattern(self, element):
        """Check if an element is a node pattern."""
        # Node pattern has at least 1 element (variable), and can have labels and properties
        # But it should not be a relationship pattern
        if not (hasattr(element, '__len__') and len(element) >= 1):
            return False

        # Check if it's NOT a relationship pattern
        # Relationship patterns have nested list structure like [['WORKS_FOR']]
        first_elem = element[0]
        if hasattr(first_elem, '__len__') and not isinstance(first_elem, str) and len(first_elem) > 0:
            # This is a nested list structure (not string), likely a relationship
            return False

        # This is a simple list like ['p', 'Person'] - a node pattern
        return True

    def _is_relationship_pattern(self, element):
        """Check if an element is a relationship pattern."""
        # Relationship patterns are nested lists like [['WORKS_FOR']]
        # They have the structure: [[rel_type, ...]] or similar
        if not (hasattr(element, '__len__') and len(element) > 0):
            return False

        # Check if it's a nested list structure typical of relationships
        first_elem = element[0]
        if hasattr(first_elem, '__len__') and not isinstance(first_elem, str) and len(first_elem) > 0:
            # This looks like [['WORKS_FOR']] - a relationship pattern
            # Node patterns would be ['var', 'Label'] or ['var', {...}]
            # Relationship patterns are [['TYPE']] or similar nested structures
            return True

        return False

    def _expression_to_string(self, expr):
        """Convert an expression to a string representation."""
        if isinstance(expr, str):
            return expr
        elif hasattr(expr, '__len__'):
            if len(expr) == 2:
                first_elem = str(expr[0]).upper()
                if first_elem in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE', 'SUBSTRING', 'REPLACE', 'SPLIT']:
                    # Function call
                    if str(expr[1]) == '*':
                        return f"{expr[0]}(*)"
                    elif hasattr(expr[1], '__len__') and len(expr[1]) == 2:
                        return f"{expr[0]}({expr[1][0]}.{expr[1][1]})"
                    else:
                        return f"{expr[0]}({expr[1]})"
                else:
                    # Property access
                    return f"{expr[0]}.{expr[1]}"
            elif len(expr) == 3 and str(expr[0]).upper() in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'REVERSE', 'SUBSTRING', 'REPLACE', 'SPLIT']:
                return f"{expr[0]}({expr[1]})"
        return str(expr)

    def _apply_ordering(self, results, columns, order_clause):
        """Apply ORDER BY to results."""
        order_items = order_clause[2:]  # Skip ORDER BY keywords

        if not order_items or not results:
            return results

        # Create sort keys
        def sort_key(row):
            keys = []
            for order_item in order_items:
                if isinstance(order_item, list) and len(order_item) >= 1:
                    expr = order_item[0]
                    desc = len(order_item) > 1 and str(order_item[1]).upper() == 'DESC'

                    # Find the column index
                    col_name = self._expression_to_string(expr)
                    try:
                        col_index = columns.index(col_name)
                        value = row[col_index]
                        # Handle None values
                        if value is None:
                            value = float('-in') if not desc else float('inf')
                        keys.append(value if not desc else -value if isinstance(value, (int, float)) else value)
                    except (ValueError, IndexError):
                        keys.append(0)
            return keys

        try:
            return sorted(results, key=sort_key)
        except TypeError:
            # If sorting fails due to incompatible types, return original results
            return results

    def _handle_variable_length_path(self, start_node, rel_pattern, target_pattern, 
                                   min_hops, max_hops, current_binding, nodes, relationships, node_index):
        """Handle variable-length path matching."""
        valid_paths = []
        
        # Find all possible target nodes within the hop range
        path_results = self._find_variable_length_paths(
            start_node, rel_pattern, target_pattern, min_hops, max_hops
        )
        
        for target_node, path_length, path_rels in path_results:
            # Create new binding with the target node
            new_binding = current_binding.copy()
            
            # Set the target node variable if it exists
            next_node_var = target_pattern[0] if len(target_pattern) > 0 else None
            if next_node_var:
                new_binding[str(next_node_var)] = target_node
            
            # Store relationship path if the relationship has a variable
            rel_var = self._get_relationship_variable(rel_pattern)
            if rel_var:
                # For variable-length paths, store the list of relationships
                new_binding[str(rel_var)] = path_rels
            
            # Continue with the rest of the path (skip to next node pair)
            if node_index + 1 < len(nodes) - 1:
                sub_paths = self._find_valid_paths(nodes, relationships, new_binding, node_index + 1)
                valid_paths.extend(sub_paths)
            else:
                # This was the last relationship in the pattern
                valid_paths.append(new_binding)
        
        return valid_paths

    def _parse_variable_length(self, rel_detail):
        """Parse variable-length specification from relationship detail.
        
        Returns:
            tuple: (min_hops, max_hops) or None if not variable-length
        """
        if not rel_detail or len(rel_detail) == 0:
            return None
            
        # The structure is like [['KNOWS', 2]] - we need to extract the inner list
        # rel_detail is [['KNOWS', 2]], so rel_detail[0] is ['KNOWS', 2]
        # Note: pyparsing returns ParseResults objects, not regular lists
        if len(rel_detail) > 0 and hasattr(rel_detail[0], '__len__'):
            inner_detail = rel_detail[0]  # This should be ['KNOWS', 2]
        else:
            inner_detail = rel_detail
            
        # Now check the inner structure: ['KNOWS', 2] or ['KNOWS', 1, 3] or ['KNOWS']
        if len(inner_detail) >= 3:
            # Check for range hops: ['KNOWS', 1, 3] - check this first
            if isinstance(inner_detail[1], int) and isinstance(inner_detail[2], int):
                return (inner_detail[1], inner_detail[2])
        
        if len(inner_detail) >= 2:
            # Check for exact hops: ['KNOWS', 2] or unlimited: ['KNOWS', '*']
            if isinstance(inner_detail[1], int):
                return (inner_detail[1], inner_detail[1])
            elif str(inner_detail[1]) == '*':
                # Unlimited variable-length path
                return (1, 10)  # Reasonable default limit for unlimited
        
        # Regular relationship (no variable-length)
        return None

    def _find_variable_length_paths(self, start_node, rel_pattern, target_pattern, min_hops, max_hops, visited=None):
        """Find all paths of variable length between nodes.
        
        Args:
            start_node: Starting node
            rel_pattern: Relationship pattern to match
            target_pattern: Target node pattern to match
            min_hops: Minimum number of hops
            max_hops: Maximum number of hops
            visited: Set of visited node IDs to avoid cycles
            
        Returns:
            List of (target_node, path_length, relationships) tuples
        """
        if visited is None:
            visited = set()
            
        if start_node['id'] in visited:
            return []  # Avoid cycles
            
        visited = visited.copy()
        # Don't add start_node to visited yet - allow self-loops for min_hops <= 0
        
        results = []
        
        # If we're at minimum hops, check if current node matches target
        if min_hops <= 0:
            if self._node_matches_pattern(start_node, target_pattern):
                results.append((start_node, 0, []))
        
        # If we haven't reached max hops, continue traversing
        if max_hops > 0:
            # Add start_node to visited now to prevent infinite cycles
            visited.add(start_node['id'])
            
            all_relationships = self.graph_db.find_relationships()
            
            for rel in all_relationships:
                if self._relationship_matches_pattern(rel, rel_pattern, start_node['id']):
                    # Find the next node
                    next_node_id = None
                    if rel['source'] == start_node['id']:
                        next_node_id = rel['target']
                    elif rel['target'] == start_node['id']:
                        # For undirected or reverse traversal
                        next_node_id = rel['source']
                    
                    if next_node_id is not None:
                        # Allow self-loops only if we haven't visited this node in the current path
                        # or if it's a self-loop and we're at the minimum hop count
                        can_traverse = (next_node_id not in visited or 
                                      (next_node_id == start_node['id'] and min_hops <= 1))
                        
                        if can_traverse:
                            next_node = self.graph_db.get_node(next_node_id)
                            if next_node:
                                # For self-loops, don't pass the current node in visited
                                # to allow it to be a valid target
                                next_visited = visited.copy()
                                if next_node_id == start_node['id']:
                                    # Self-loop: remove the current node from visited for the recursive call
                                    next_visited.discard(start_node['id'])
                                
                                # Recursively find paths from the next node
                                sub_paths = self._find_variable_length_paths(
                                    next_node, rel_pattern, target_pattern,
                                    max(0, min_hops - 1), max_hops - 1, next_visited
                                )
                                
                                # Add current relationship to each sub-path
                                for target_node, path_length, path_rels in sub_paths:
                                    new_path_rels = [rel] + path_rels
                                    results.append((target_node, path_length + 1, new_path_rels))
        
        return results
