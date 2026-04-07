"""
Enhanced NLP Keyword Extractor
Extracts keywords, entities, and intent from natural language queries
"""

from rapidfuzz import process, fuzz
import re
from typing import Dict, List, Tuple, Optional

class NLPExtractor:
    """Enhanced NLP extraction with multi-strategy keyword detection"""

    # Database schema definition (Expanded)
    SCHEMA = {
        "students": {
            "columns": ["id", "name", "cgpa", "marks", "year", "age", "email", "phone", "address", "enrollment_date", "major", "semester", "gpa", "attendance_percentage", "scholarship_amount", "is_active", "department", "city", "country", "gender"],
            "numeric_columns": ["cgpa", "marks", "year", "age", "semester", "gpa", "attendance_percentage", "scholarship_amount"],
            "string_columns": ["name", "email", "phone", "address", "major", "department", "city", "country", "gender"],
            "date_columns": ["enrollment_date"],
            "boolean_columns": ["is_active"],
            "aliases": ["student", "pupils", "learners", "scholars", "undergrads", "graduates"],
            "description": "Student information including academic performance and personal details",
            "primary_key": "id",
            "sortable_columns": ["cgpa", "marks", "gpa", "year", "age", "attendance_percentage", "scholarship_amount"],
            "filterable_columns": ["year", "major", "semester", "is_active", "cgpa", "marks", "department", "city", "country", "gender"],
            "default_display_columns": ["id", "name", "cgpa", "marks", "year"]
        },
        "cars": {
            "columns": ["id", "car_name", "brand", "model", "price", "units_sold", "year", "color", "fuel_type", "transmission", "mileage", "engine_capacity", "horsepower", "seats", "rating", "manufacturing_date", "is_available"],
            "numeric_columns": ["price", "units_sold", "year", "mileage", "engine_capacity", "horsepower", "seats", "rating"],
            "string_columns": ["car_name", "brand", "model", "color", "fuel_type", "transmission"],
            "date_columns": ["manufacturing_date"],
            "boolean_columns": ["is_available"],
            "aliases": ["car", "vehicles", "automobiles", "autos", "vehicle"],
            "description": "Car inventory with specifications and sales data",
            "primary_key": "id",
            "sortable_columns": ["price", "units_sold", "year", "mileage", "rating", "horsepower"],
            "filterable_columns": ["brand", "fuel_type", "transmission", "year", "color", "is_available"],
            "default_display_columns": ["id", "car_name", "brand", "price", "year"]
        },
        "employees": {
            "columns": ["id", "name", "email", "phone", "salary", "department", "position", "year_joined", "hire_date", "rating", "age", "experience_years", "bonus", "commission", "manager_id", "office_location", "is_active", "employment_type", "level", "city", "country", "gender", "year", "experience"],
            "numeric_columns": ["salary", "year_joined", "rating", "age", "experience_years", "bonus", "commission", "manager_id", "level", "year", "experience"],
            "string_columns": ["name", "email", "phone", "department", "position", "office_location", "employment_type", "city", "country", "gender"],
            "date_columns": ["hire_date"],
            "boolean_columns": ["is_active"],
            "aliases": ["employee", "staff", "workers", "personnel", "team members", "workforce"],
            "description": "Employee records with compensation and organizational details",
            "primary_key": "id",
            "foreign_keys": {"manager_id": "employees.id"},
            "sortable_columns": ["salary", "rating", "year_joined", "experience_years", "age", "bonus", "level", "experience"],
            "filterable_columns": ["department", "position", "year_joined", "office_location", "is_active", "employment_type", "level", "city", "country", "gender"],
            "default_display_columns": ["id", "name", "department", "position", "salary"]
        },
        "products": {
            "columns": ["id", "product_name", "brand", "category", "subcategory", "price", "cost_price", "quantity", "rating", "reviews_count", "weight", "dimensions", "color", "manufacturer", "launch_date", "expiry_date", "discount_percentage", "is_available", "warehouse_location", "status", "stock", "name", "description", "in_stock"],
            "numeric_columns": ["price", "cost_price", "quantity", "rating", "reviews_count", "weight", "discount_percentage", "stock"],
            "string_columns": ["product_name", "brand", "category", "subcategory", "dimensions", "color", "manufacturer", "warehouse_location", "status", "name", "description"],
            "date_columns": ["launch_date", "expiry_date"],
            "boolean_columns": ["is_available", "in_stock"],
            "aliases": ["product", "items", "goods", "merchandise", "inventory", "stock"],
            "description": "Product catalog with pricing, inventory, and specifications",
            "primary_key": "id",
            "sortable_columns": ["price", "quantity", "rating", "reviews_count", "discount_percentage", "stock"],
            "filterable_columns": ["category", "subcategory", "brand", "is_available", "color", "warehouse_location", "status"],
            "default_display_columns": ["id", "product_name", "category", "price", "quantity"]
        },
        "orders": {
            "columns": ["id", "order_number", "customer_id", "product_id", "quantity", "total_amount", "discount_amount", "tax_amount", "final_amount", "order_date", "delivery_date", "status", "payment_method", "shipping_address", "is_paid", "is_delivered"],
            "numeric_columns": ["customer_id", "product_id", "quantity", "total_amount", "discount_amount", "tax_amount", "final_amount"],
            "string_columns": ["order_number", "status", "payment_method", "shipping_address"],
            "date_columns": ["order_date", "delivery_date"],
            "boolean_columns": ["is_paid", "is_delivered"],
            "aliases": ["order", "purchase", "transaction", "sale", "orders"],
            "description": "Customer orders with payment and delivery information",
            "primary_key": "id",
            "foreign_keys": {"customer_id": "customers.id", "product_id": "products.id"},
            "sortable_columns": ["total_amount", "final_amount", "order_date", "quantity"],
            "filterable_columns": ["status", "payment_method", "is_paid", "is_delivered", "order_date"],
            "default_display_columns": ["id", "order_number", "customer_id", "total_amount", "order_date", "status"]
        },
        "customers": {
            "columns": ["id", "name", "email", "phone", "address", "city", "state", "country", "postal_code", "registration_date", "last_purchase_date", "total_purchases", "total_spent", "loyalty_points", "customer_tier", "is_active", "age", "gender"],
            "numeric_columns": ["total_purchases", "total_spent", "loyalty_points", "age"],
            "string_columns": ["name", "email", "phone", "address", "city", "state", "country", "postal_code", "customer_tier", "gender"],
            "date_columns": ["registration_date", "last_purchase_date"],
            "boolean_columns": ["is_active"],
            "aliases": ["customer", "client", "buyer", "shopper", "customers"],
            "description": "Customer profiles with purchase history and loyalty information",
            "primary_key": "id",
            "sortable_columns": ["total_purchases", "total_spent", "loyalty_points", "registration_date", "age"],
            "filterable_columns": ["city", "state", "country", "customer_tier", "is_active", "gender"],
            "default_display_columns": ["id", "name", "email", "total_purchases", "total_spent"]
        },
        "departments": {
            "columns": ["id", "department_name", "department_code", "manager_id", "budget", "employee_count", "location", "floor_number", "established_date", "is_active"],
            "numeric_columns": ["manager_id", "budget", "employee_count", "floor_number"],
            "string_columns": ["department_name", "department_code", "location"],
            "date_columns": ["established_date"],
            "boolean_columns": ["is_active"],
            "aliases": ["department", "dept", "division", "section", "unit"],
            "description": "Organizational departments with budget and staffing information",
            "primary_key": "id",
            "foreign_keys": {"manager_id": "employees.id"},
            "sortable_columns": ["budget", "employee_count", "established_date"],
            "filterable_columns": ["location", "is_active", "floor_number"],
            "default_display_columns": ["id", "department_name", "manager_id", "budget", "employee_count"]
        },
        "projects": {
            "columns": ["id", "project_name", "project_code", "description", "manager_id", "department_id", "budget", "spent_amount", "start_date", "end_date", "deadline", "status", "priority", "completion_percentage", "team_size", "is_active"],
            "numeric_columns": ["manager_id", "department_id", "budget", "spent_amount", "completion_percentage", "team_size"],
            "string_columns": ["project_name", "project_code", "description", "status", "priority"],
            "date_columns": ["start_date", "end_date", "deadline"],
            "boolean_columns": ["is_active"],
            "aliases": ["project", "initiative", "program", "assignment", "projects"],
            "description": "Project tracking with budget, timeline, and completion status",
            "primary_key": "id",
            "foreign_keys": {"manager_id": "employees.id", "department_id": "departments.id"},
            "sortable_columns": ["budget", "spent_amount", "completion_percentage", "start_date", "deadline", "team_size"],
            "filterable_columns": ["status", "priority", "is_active", "department_id"],
            "default_display_columns": ["id", "project_name", "status", "budget", "completion_percentage"]
        },
        "courses": {
            "columns": ["id", "course_name", "course_code", "credits", "instructor_id", "department", "semester", "year", "max_students", "enrolled_students", "room_number", "schedule", "duration_hours", "difficulty_level", "is_active"],
            "numeric_columns": ["credits", "instructor_id", "year", "max_students", "enrolled_students", "duration_hours"],
            "string_columns": ["course_name", "course_code", "department", "semester", "room_number", "schedule", "difficulty_level"],
            "date_columns": [],
            "boolean_columns": ["is_active"],
            "aliases": ["course", "class", "subject", "module", "courses"],
            "description": "Academic courses with enrollment and scheduling information",
            "primary_key": "id",
            "foreign_keys": {"instructor_id": "employees.id"},
            "sortable_columns": ["credits", "enrolled_students", "year", "max_students", "duration_hours"],
            "filterable_columns": ["department", "semester", "year", "difficulty_level", "is_active"],
            "default_display_columns": ["id", "course_name", "course_code", "credits", "instructor_id"]
        },
        "suppliers": {
            "columns": ["id", "supplier_name", "contact_person", "email", "phone", "address", "city", "country", "rating", "total_orders", "total_value", "payment_terms", "delivery_time_days", "is_active", "registration_date"],
            "numeric_columns": ["rating", "total_orders", "total_value", "delivery_time_days"],
            "string_columns": ["supplier_name", "contact_person", "email", "phone", "address", "city", "country", "payment_terms"],
            "date_columns": ["registration_date"],
            "boolean_columns": ["is_active"],
            "aliases": ["supplier", "vendor", "provider", "distributor", "suppliers"],
            "description": "Supplier information with performance and transaction history",
            "primary_key": "id",
            "sortable_columns": ["rating", "total_orders", "total_value", "delivery_time_days"],
            "filterable_columns": ["city", "country", "is_active", "payment_terms"],
            "default_display_columns": ["id", "supplier_name", "rating", "total_orders", "total_value"]
        }
    }

    # Intent keywords
    RANKING_KEYWORDS = {
        "top": ("DESC", ["highest", "best", "top", "maximum", "largest", "greatest", "most"]),
        "bottom": ("ASC", ["lowest", "worst", "bottom", "minimum", "smallest", "least", "fewest"])
    }

    AGGREGATION_KEYWORDS = {
        "AVG": ["average", "avg", "mean"],
        "SUM": ["total", "sum", "add up", "combined"],
        "COUNT": ["count", "number of", "how many", "total number"],
        "MAX": ["maximum", "max", "highest", "largest", "greatest"],
        "MIN": ["minimum", "min", "lowest", "smallest", "least"]
    }

    COMPARISON_OPERATORS = {
        ">": ["greater than", "more than", "above", "over", "exceeds", "higher than"],
        "<": ["less than", "below", "under", "fewer than", "lower than"],
        ">=": ["at least", "minimum of", "no less than", "or more"],
        "<=": ["at most", "maximum of", "no more than", "or less"],
        "=": ["equals", "equal to", "is", "exactly"],
        "!=": ["not equal to", "not", "different from"]
    }

    # Column synonyms for better matching (Expanded)
    COLUMN_SYNONYMS = {
        # Students columns
        "cgpa": ["gpa", "grade point", "grade", "grades", "cumulative gpa"],
        "marks": ["score", "scores", "points", "mark", "test score"],
        "age": ["years old", "student age"],
        "semester": ["sem", "term", "period"],
        "major": ["specialization", "field", "stream", "branch", "course"],
        "attendance_percentage": ["attendance", "present percentage", "presence"],
        "scholarship_amount": ["scholarship", "financial aid", "grant"],

        # Cars columns
        "car_name": ["vehicle", "car", "automobile", "car model", "vehicle name"],
        "brand": ["make", "manufacturer", "company"],
        "model": ["variant", "version", "type"],
        "fuel_type": ["fuel", "petrol", "diesel", "gas type"],
        "transmission": ["gearbox", "gear type", "manual", "automatic"],
        "mileage": ["fuel efficiency", "kmpl", "mpg", "efficiency"],
        "engine_capacity": ["engine size", "cc", "displacement"],
        "horsepower": ["hp", "power", "bhp"],
        "units_sold": ["sales", "sold", "units", "quantity sold", "sold units"],

        # Employees columns
        "name": ["student name", "employee name", "staff name", "worker name", "person name"],
        "salary": ["wage", "wages", "pay", "income", "compensation", "remuneration"],
        "department": ["dept", "division", "section", "unit"],
        "position": ["role", "title", "designation", "job title"],
        "year_joined": ["joining year", "hire year", "start year"],
        "experience_years": ["experience", "years of experience", "work experience", "tenure"],
        "bonus": ["incentive", "bonus pay", "extra pay"],
        "commission": ["sales commission", "percentage"],
        "manager_id": ["manager", "supervisor", "boss"],
        "office_location": ["location", "office", "branch"],
        "employment_type": ["type", "full time", "part time", "contract"],
        "rating": ["performance", "rating score", "evaluation", "review score"],

        # Products columns
        "product_name": ["product", "item", "item name", "product title"],
        "price": ["cost", "costing", "value", "amount", "pricing", "price tag"],
        "cost_price": ["purchase price", "wholesale price", "buying price"],
        "quantity": ["stock", "available", "in stock", "qty", "inventory"],
        "rating": ["rate", "rated", "score", "review score", "stars"],
        "reviews_count": ["reviews", "review count", "number of reviews"],
        "weight": ["mass", "item weight"],
        "category": ["type", "kind", "class", "group"],
        "subcategory": ["subtype", "subclass", "subgroup"],
        "discount_percentage": ["discount", "off", "sale", "reduction"],
        "warehouse_location": ["warehouse", "storage", "location"],

        # Orders columns
        "order_number": ["order id", "order code", "order ref"],
        "customer_id": ["customer", "buyer", "client"],
        "product_id": ["product", "item"],
        "total_amount": ["amount", "total", "order amount", "order total", "order value", "sum"],
        "discount_amount": ["discount", "discount value", "savings"],
        "tax_amount": ["tax", "gst", "vat"],
        "final_amount": ["final total", "final price", "amount paid", "net amount"],
        "order_date": ["date", "purchase date", "order time"],
        "delivery_date": ["delivered date", "shipping date"],
        "status": ["order status", "state", "condition"],
        "payment_method": ["payment", "payment type", "payment mode"],
        "is_paid": ["paid", "payment status"],
        "is_delivered": ["delivered", "delivery status"],

        # Customers columns
        "total_purchases": ["purchases", "orders", "number of orders"],
        "total_spent": ["spent", "spending", "expenditure", "total amount"],
        "loyalty_points": ["points", "reward points", "rewards"],
        "customer_tier": ["tier", "level", "status"],
        "city": ["town", "location"],
        "state": ["province", "region"],
        "postal_code": ["zip", "pincode", "zip code"],
        "gender": ["sex"],
        "registration_date": ["registered date", "signup date", "joined date"],

        # Departments columns
        "department_name": ["department", "dept name"],
        "department_code": ["dept code", "code"],
        "budget": ["fund", "allocation", "funding"],
        "employee_count": ["employees", "staff count", "headcount", "team size"],
        "floor_number": ["floor", "level"],

        # Projects columns
        "project_name": ["project", "project title"],
        "project_code": ["code", "project id"],
        "spent_amount": ["spent", "expenditure", "used budget"],
        "start_date": ["start", "begin date", "commenced"],
        "end_date": ["end", "finish date", "completed date"],
        "deadline": ["due date", "target date"],
        "priority": ["importance", "urgency"],
        "completion_percentage": ["completion", "progress", "done percentage"],
        "team_size": ["team members", "team count", "members"],

        # Courses columns
        "course_name": ["course", "class", "subject"],
        "course_code": ["code", "course id"],
        "credits": ["credit hours", "units"],
        "instructor_id": ["instructor", "teacher", "professor"],
        "max_students": ["capacity", "maximum"],
        "enrolled_students": ["enrolled", "students", "enrollment"],
        "room_number": ["room", "classroom"],
        "schedule": ["timing", "time", "timetable"],
        "duration_hours": ["duration", "hours", "class hours"],
        "difficulty_level": ["difficulty", "level"],

        # Suppliers columns
        "supplier_name": ["supplier", "vendor", "provider"],
        "contact_person": ["contact", "representative", "contact name"],
        "total_orders": ["orders", "purchase orders"],
        "total_value": ["value", "order value", "purchase value"],
        "payment_terms": ["terms", "payment conditions"],
        "delivery_time_days": ["delivery time", "lead time", "shipping time"],

        # Common columns
        "email": ["mail", "email address", "e-mail"],
        "phone": ["phone number", "contact number", "mobile", "telephone"],
        "address": ["location", "street address"],
        "country": ["nation"],
        "is_active": ["active", "status", "enabled"],
        "description": ["desc", "details", "info"]
    }

    def __init__(self):
        """Initialize the NLP extractor"""
        self.reverse_synonyms = self._build_reverse_synonyms()

    def _build_reverse_synonyms(self) -> Dict[str, str]:
        """Build reverse mapping from synonyms to canonical column names"""
        reverse = {}
        for canonical, synonyms in self.COLUMN_SYNONYMS.items():
            reverse[canonical] = canonical
            for synonym in synonyms:
                reverse[synonym] = canonical
        return reverse

    def extract_keywords(self, query: str, original_query: str = None) -> Dict:
        """
        Main extraction method - extracts all keywords and entities from query

        Args:
            query: Preprocessed query (for table/column matching)
            original_query: Original query with preserved case (for filter values)

        Returns:
            Dict with table, columns, aggregation, filters, ranking, etc.
        """
        # Use original query if provided, otherwise use the preprocessed query
        if original_query is None:
            original_query = query

        query_lower = query.lower()

        # Extract all components
        table_info = self._extract_table(query_lower)
        columns_info = self._extract_columns(query_lower, table_info['table'])
        aggregation_info = self._extract_aggregation(query_lower)
        ranking_info = self._extract_ranking(query_lower)
        # Use original query for filters to preserve case (e.g., "IT" not "it")
        filters_info = self._extract_filters(original_query, table_info['table'])
        calculation_info = self._extract_calculations(query_lower, table_info['table'])

        # Build comprehensive result
        result = {
            "table": table_info['table'],
            "table_confidence": table_info['confidence'],
            "primary_column": columns_info['primary'],
            "column_confidence": columns_info['confidence'],
            "all_mentioned_columns": columns_info['all_columns'],
            "aggregation": aggregation_info['function'],
            "aggregation_confidence": aggregation_info['confidence'],
            "ranking_direction": ranking_info['direction'],
            "limit": ranking_info['limit'],
            "filters": filters_info['conditions'],
            "filter_confidence": filters_info['confidence'],
            "has_calculation": calculation_info['has_calculation'],
            "calculation": calculation_info['expression'],
            "calculation_columns": calculation_info['columns'],
            "intent": self._determine_intent(aggregation_info, ranking_info, filters_info, calculation_info),
            "original_query": query
        }

        return result

    def _extract_table(self, query: str) -> Dict:
        """Extract table name with fuzzy matching and column context awareness"""
        all_table_names = []
        for table_name, info in self.SCHEMA.items():
            all_table_names.append(table_name)
            all_table_names.extend(info['aliases'])

        # Try exact word matching first
        words = query.split()
        for word in words:
            if word in all_table_names:
                canonical = self._get_canonical_table_name(word)
                return {"table": canonical, "confidence": 100.0}

        # Strategy: Column-based table inference (HIGHEST PRIORITY)
        # E.g., "Maximum salary in IT department" mentions "salary" which is in employees table
        # This prevents picking "departments" table just because "department" is mentioned
        table_scores = {}
        for table_name, info in self.SCHEMA.items():
            score = 0
            # Check if any columns from this table are mentioned
            for col in info['columns']:
                # Normalize column name (remove underscores for matching)
                col_normalized = col.replace('_', ' ')

                # Exact column match (with or without underscores)
                if col in query or col_normalized in query:
                    # Prioritize numeric columns for aggregation queries
                    if col in info.get('numeric_columns', []):
                        score += 120
                    else:
                        score += 100
                # Synonym match
                elif col in self.COLUMN_SYNONYMS:
                    for syn in self.COLUMN_SYNONYMS[col]:
                        if syn in query:
                            if col in info.get('numeric_columns', []):
                                score += 100
                            else:
                                score += 80
                            break

            table_scores[table_name] = score

        # If we found strong column evidence, use that
        if table_scores:
            best_table = max(table_scores, key=table_scores.get)
            if table_scores[best_table] >= 80:
                return {"table": best_table, "confidence": min(100.0, float(table_scores[best_table]))}

        # Fuzzy matching fallback (table name matching)
        result = process.extractOne(
            query,
            all_table_names,
            scorer=fuzz.partial_ratio,
            score_cutoff=60.0
        )

        if result:
            matched_name, confidence, _ = result
            canonical = self._get_canonical_table_name(matched_name)
            return {"table": canonical, "confidence": float(confidence)}

        return {"table": None, "confidence": 0.0}

    def _get_canonical_table_name(self, name: str) -> Optional[str]:
        """Get canonical table name from alias"""
        for table_name, info in self.SCHEMA.items():
            if name == table_name or name in info['aliases']:
                return table_name
        return None

    def _extract_columns(self, query: str, table: Optional[str]) -> Dict:
        """Extract columns mentioned in query with multi-strategy detection"""
        if not table or table not in self.SCHEMA:
            return {"primary": None, "confidence": 0.0, "all_columns": []}

        available_columns = self.SCHEMA[table]['columns']
        detected_columns = []
        max_confidence = 0.0
        primary_column = None

        # Strategy 0: EXACT word boundary matching (HIGHEST PRIORITY)
        # This catches exact column names like "marks", "salary", "cgpa", "completion_percentage"
        for col in available_columns:
            # Try exact match with underscores
            pattern = r'\b' + re.escape(col) + r'\b'
            if re.search(pattern, query):
                detected_columns.append(col)
                if not primary_column:
                    primary_column = col
                    max_confidence = 100.0

            # Also try with underscores replaced by spaces
            col_with_spaces = col.replace('_', ' ')
            if col != col_with_spaces:
                pattern_spaces = r'\b' + re.escape(col_with_spaces) + r'\b'
                if re.search(pattern_spaces, query):
                    if col not in detected_columns:
                        detected_columns.append(col)
                    if not primary_column:
                        primary_column = col
                        max_confidence = 100.0

        # Strategy 1: Aggregation context (SECOND PRIORITY for aggregation queries)
        # E.g., "average marks", "total salary", "maximum price"
        # This helps "Maximum salary in IT department" select "salary", not "department"
        for agg_func, keywords in self.AGGREGATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    # Look for numeric columns mentioned near aggregation keyword
                    column_scores = {}
                    for col in self.SCHEMA[table]['numeric_columns']:
                        # Normalize for matching (remove underscores)
                        col_normalized = col.replace('_', ' ')

                        # Check exact match (with and without underscores)
                        # IMPORTANT: Use word boundary to avoid matching "age" in "average"
                        col_pos = -1
                        matched_term = None

                        # Try word boundary match for column name
                        pattern = r'\b' + re.escape(col) + r'\b'
                        match = re.search(pattern, query)
                        if match:
                            col_pos = match.start()
                            matched_term = col
                        elif col != col_normalized:
                            # Try with spaces
                            pattern_spaces = r'\b' + re.escape(col_normalized) + r'\b'
                            match = re.search(pattern_spaces, query)
                            if match:
                                col_pos = match.start()
                                matched_term = col_normalized

                        # Check synonyms only if no direct match
                        if col_pos == -1:
                            for syn in self.COLUMN_SYNONYMS.get(col, []):
                                if syn in query:
                                    col_pos = query.find(syn)
                                    matched_term = syn
                                    break

                        if col_pos != -1:
                            # Calculate proximity to aggregation keyword
                            keyword_pos = query.find(keyword)
                            proximity = abs(keyword_pos - col_pos)

                            # Score based on proximity and match quality
                            score = 1000 - proximity  # Closer is better

                            # Bonus for exact match vs synonym
                            if matched_term == col or matched_term == col_normalized:
                                score += 100

                            column_scores[col] = score

                    # Select column with highest score
                    # Prefer aggregation context over exact match if score is high enough
                    if column_scores:
                        best_col = max(column_scores, key=column_scores.get)
                        best_score = column_scores[best_col]

                        # Only override exact match if aggregation context has high confidence
                        # and the current primary_column has low proximity to aggregation keyword
                        if not primary_column or best_score > 1050:  # High confidence threshold
                            if best_col not in detected_columns:
                                detected_columns.append(best_col)
                            primary_column = best_col
                            max_confidence = 95.0

        # Strategy 2: Synonym matching
        if not primary_column:
            words = query.split()
            for word in words:
                if word in self.reverse_synonyms:
                    canonical_col = self.reverse_synonyms[word]
                    if canonical_col in available_columns and canonical_col not in detected_columns:
                        detected_columns.append(canonical_col)
                        if not primary_column:
                            primary_column = canonical_col
                            max_confidence = 95.0

        # Strategy 4: Ranking context (for ranking queries like "find X with highest/lowest Y")
        # E.g., "Find 4 suppliers with lowest delivery time" should extract "delivery_time_days"
        if not primary_column:
            for rank_type, (rank_dir, keywords) in self.RANKING_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in query:
                        # Look for sortable columns mentioned after ranking keyword
                        sortable_cols = self.SCHEMA[table].get('sortable_columns', self.SCHEMA[table]['numeric_columns'])
                        for col in sortable_cols:
                            # Check if column or its synonym appears after the ranking keyword
                            if col in query or any(syn in query for syn in self.COLUMN_SYNONYMS.get(col, [])):
                                if col not in detected_columns:
                                    detected_columns.append(col)
                                if not primary_column:
                                    primary_column = col
                                    max_confidence = 90.0
                                    break

        # Strategy 5: Fuzzy matching as last resort
        if not primary_column:
            result = process.extractOne(
                query,
                available_columns,
                scorer=fuzz.partial_ratio,
                score_cutoff=70.0
            )
            if result:
                col, confidence, _ = result
                primary_column = col
                max_confidence = float(confidence)
                if col not in detected_columns:
                    detected_columns.append(col)

        return {
            "primary": primary_column,
            "confidence": max_confidence,
            "all_columns": detected_columns
        }

    def _extract_aggregation(self, query: str) -> Dict:
        """Extract aggregation function if present"""
        # Collect all potential matches across all functions
        # E.g., "total number" should match COUNT (longer), not SUM (from "total")
        matches = []
        for agg_func, keywords in self.AGGREGATION_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundary matching to avoid false matches like "in count" in "in country"
                # Special handling for multi-word keywords like "number of"
                if ' ' in keyword:
                    # For multi-word keywords, just check if they're in the query
                    if keyword in query:
                        matches.append((agg_func, keyword, len(keyword)))
                else:
                    # For single-word keywords, use word boundaries
                    # This prevents "count" from matching "country" or "in count" from matching "in country"
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, query, re.IGNORECASE):
                        matches.append((agg_func, keyword, len(keyword)))

        # If we found matches, return the one with the longest keyword
        if matches:
            # Sort by keyword length (descending)
            matches.sort(key=lambda x: x[2], reverse=True)
            best_func = matches[0][0]
            return {"function": best_func, "confidence": 95.0}

        return {"function": None, "confidence": 0.0}

    def _extract_ranking(self, query: str) -> Dict:
        """Extract ranking direction and limit"""
        direction = None
        limit = None

        # Check for ranking keywords
        for rank_type, (rank_dir, keywords) in self.RANKING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    direction = rank_dir
                    break
            if direction:
                break

        # Build comprehensive list of table names for limit extraction
        all_table_terms = []
        for table_name, info in self.SCHEMA.items():
            all_table_terms.append(table_name)
            all_table_terms.extend(info['aliases'])

        # Create dynamic pattern for all table names
        table_pattern = '|'.join(re.escape(term) for term in all_table_terms)

        # Extract limit number with comprehensive patterns
        limit_patterns = [
            r'top\s+(\d+)',
            r'bottom\s+(\d+)',
            r'highest\s+(\d+)',
            r'lowest\s+(\d+)',
            r'best\s+(\d+)',
            r'worst\s+(\d+)',
            r'first\s+(\d+)',
            r'last\s+(\d+)',
            r'show\s+(\d+)',
            r'get\s+(\d+)',
            r'find\s+(\d+)',
            r'(\d+)\s+(?:' + table_pattern + r')',  # Dynamic pattern for all tables
        ]

        for pattern in limit_patterns:
            match = re.search(pattern, query)
            if match:
                limit = int(match.group(1))
                break

        return {"direction": direction, "limit": limit}

    def _extract_filters(self, query: str, table: Optional[str]) -> Dict:
        """
        Extract WHERE conditions and filters
        Uses case-insensitive matching but preserves original case in extracted values
        """
        conditions = []
        confidence = 0.0

        if not table or table not in self.SCHEMA:
            return {"conditions": conditions, "confidence": confidence}

        # Extract comparison filters (e.g., "salary > 50000")
        for operator, keywords in self.COMPARISON_OPERATORS.items():
            for keyword in keywords:
                pattern = rf'(\w+)\s+{re.escape(keyword)}\s+([0-9.]+)'
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    column = match.group(1)
                    value = match.group(2)

                    # Normalize column name
                    if column in self.reverse_synonyms:
                        column = self.reverse_synonyms[column]

                    if column in self.SCHEMA[table]['columns']:
                        conditions.append({
                            "column": column,
                            "operator": operator,
                            "value": value,
                            "type": "comparison"
                        })
                        confidence = 90.0

        # Extract BETWEEN filters
        between_pattern = r'(\w+)\s+between\s+([0-9.]+)\s+and\s+([0-9.]+)'
        match = re.search(between_pattern, query, re.IGNORECASE)
        if match:
            column = match.group(1)
            value1 = match.group(2)
            value2 = match.group(3)

            if column in self.reverse_synonyms:
                column = self.reverse_synonyms[column]

            if column in self.SCHEMA[table]['columns']:
                conditions.append({
                    "column": column,
                    "operator": "BETWEEN",
                    "value": [value1, value2],
                    "type": "range"
                })
                confidence = 95.0

        # Extract string equality filters (e.g., "department = Engineering")
        # Pattern 1: "in department Engineering" or "of department IT"
        # Pattern 2: "in Engineering department" or "in IT department"
        # Use case-insensitive matching but preserve captured value case
        # IMPORTANT: Don't match if followed by comma (that's an IN operator)
        dept_pattern1 = r'(?:in|from|of)\s+(?:department|dept|division)\s+(\w+)(?![\s,]*,)'
        dept_pattern2 = r'(?:in|from|of)\s+(\w+)\s+(?:department|dept|division)(?![\s,]*,)'

        match1 = re.search(dept_pattern1, query, re.IGNORECASE)
        match2 = re.search(dept_pattern2, query, re.IGNORECASE)

        if (match1 or match2) and "department" in self.SCHEMA[table]['columns']:
            # Extract value with original case preserved (e.g., "IT" not "it")
            dept_value = match1.group(1) if match1 else match2.group(1)
            # Check if there's a comma nearby (IN operator case)
            if ',' not in query[max(0, match1.start() if match1 else match2.start() - 20):min(len(query), (match1.end() if match1 else match2.end()) + 20)]:
                conditions.append({
                    "column": "department",
                    "operator": "=",
                    "value": dept_value,
                    "type": "string"
                })
                confidence = 85.0

        # Extract category filters
        # Pattern 1: "in category Electronics" or "of category Food"
        # Pattern 2: "in Electronics category" or "in Food category"
        # Use case-insensitive matching but preserve captured value case
        cat_pattern1 = r'(?:in|from|of)\s+(?:category|type)\s+(\w+)'
        cat_pattern2 = r'(?:in|from|of)\s+(\w+)\s+(?:category|type)'

        cat_match1 = re.search(cat_pattern1, query, re.IGNORECASE)
        cat_match2 = re.search(cat_pattern2, query, re.IGNORECASE)

        if (cat_match1 or cat_match2) and "category" in self.SCHEMA[table]['columns']:
            # Extract value with original case preserved
            cat_value = cat_match1.group(1) if cat_match1 else cat_match2.group(1)
            conditions.append({
                "column": "category",
                "operator": "=",
                "value": cat_value,
                "type": "string"
            })
            confidence = 85.0

        # Extract city filters (but not if comma-separated - that's IN operator)
        # Pattern: "from city Mumbai" or "in Mumbai city"
        # Use case-insensitive matching but preserve captured value case
        city_pattern1 = r'(?:from|in)\s+(?:city|town)\s+(\w+)(?!\s*,)'
        city_pattern2 = r'(?:from|in)\s+(\w+)\s+(?:city|town)(?!\s*,)'

        city_match1 = re.search(city_pattern1, query, re.IGNORECASE)
        city_match2 = re.search(city_pattern2, query, re.IGNORECASE)

        if (city_match1 or city_match2) and "city" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby (IN operator case)
            match_obj = city_match1 if city_match1 else city_match2
            if ',' not in query[match_obj.start():min(len(query), match_obj.end() + 20)]:
                # Extract value with original case preserved
                city_value = city_match1.group(1) if city_match1 else city_match2.group(1)
                conditions.append({
                    "column": "city",
                    "operator": "=",
                    "value": city_value,
                    "type": "string"
                })
                confidence = 85.0

        # Extract country filters (but not if comma-separated - that's IN operator)
        # Pattern: "from country USA" or "from India"
        country_pattern1 = r'(?:from|in)\s+(?:country)\s+(\w+)(?!\s*,)'
        country_pattern2 = r'(?:from)\s+(\w+)(?!\s*,)'  # More permissive for single value

        country_match1 = re.search(country_pattern1, query, re.IGNORECASE)
        # Only use pattern2 if no other patterns matched and "from" is present
        country_match2 = re.search(country_pattern2, query, re.IGNORECASE) if not conditions and 'from' in query else None

        if (country_match1 or country_match2) and "country" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby (IN operator case)
            match_obj = country_match1 if country_match1 else country_match2
            if match_obj and ',' not in query[match_obj.start():min(len(query), match_obj.end() + 20)]:
                country_value = country_match1.group(1) if country_match1 else country_match2.group(1)
                conditions.append({
                    "column": "country",
                    "operator": "=",
                    "value": country_value,
                    "type": "string"
                })
                confidence = 85.0

        # Extract status filters (but not if comma-separated - that's IN operator)
        # Pattern: "with status completed" or "status is pending"
        status_pattern1 = r'(?:with|has)\s+status\s+(\w+)(?!\s*,)'
        status_pattern2 = r'status\s+(?:is|=)\s+(\w+)(?!\s*,)'

        status_match1 = re.search(status_pattern1, query, re.IGNORECASE)
        status_match2 = re.search(status_pattern2, query, re.IGNORECASE)

        if (status_match1 or status_match2) and "status" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby (IN operator case)
            match_obj = status_match1 if status_match1 else status_match2
            if ',' not in query[match_obj.start():min(len(query), match_obj.end() + 20)]:
                status_value = status_match1.group(1) if status_match1 else status_match2.group(1)
                conditions.append({
                    "column": "status",
                    "operator": "=",
                    "value": status_value,
                    "type": "string"
                })
                confidence = 85.0

        # Extract year filters (but not if comma-separated - that's IN operator)
        year_pattern = r'(?:in|from|for)\s+(?:year|the year)\s+(\d{4})(?!\s*,)'
        match = re.search(year_pattern, query, re.IGNORECASE)
        if match and ',' not in query[match.start():min(len(query), match.end() + 10)]:
            year_col = "year" if "year" in self.SCHEMA[table]['columns'] else "year_joined"
            if year_col in self.SCHEMA[table]['columns']:
                conditions.append({
                    "column": year_col,
                    "operator": "=",
                    "value": match.group(1),
                    "type": "numeric"
                })
                confidence = 90.0

        # Extract semester filters (but not if comma-separated - that's IN operator)
        # Pattern: "in semester 5" or "semester 3"
        semester_pattern = r'(?:in\s+)?semester\s+(\d+)(?!\s*,)'
        match = re.search(semester_pattern, query, re.IGNORECASE)
        if match and "semester" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby
            if ',' not in query[match.start():min(len(query), match.end() + 10)]:
                conditions.append({
                    "column": "semester",
                    "operator": "=",
                    "value": match.group(1),
                    "type": "numeric"
                })
                confidence = 90.0

        # Extract level filters (but not if comma-separated - that's IN operator)
        # Pattern: "in level 3" or "level 2"
        level_pattern = r'(?:in\s+)?level\s+(\d+)(?!\s*,)'
        match = re.search(level_pattern, query, re.IGNORECASE)
        if match and "level" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby
            if ',' not in query[match.start():min(len(query), match.end() + 10)]:
                conditions.append({
                    "column": "level",
                    "operator": "=",
                    "value": match.group(1),
                    "type": "numeric"
                })
                confidence = 90.0

        # Extract brand filters
        # Pattern: "from brand Apple" or "brand is Samsung"
        brand_pattern1 = r'(?:from|of)\s+brand\s+(\w+)'
        brand_pattern2 = r'brand\s+(?:is|=)\s+(\w+)'

        brand_match1 = re.search(brand_pattern1, query, re.IGNORECASE)
        brand_match2 = re.search(brand_pattern2, query, re.IGNORECASE)

        if (brand_match1 or brand_match2) and "brand" in self.SCHEMA[table]['columns']:
            brand_value = brand_match1.group(1) if brand_match1 else brand_match2.group(1)
            conditions.append({
                "column": "brand",
                "operator": "=",
                "value": brand_value,
                "type": "string"
            })
            confidence = 85.0

        # Extract gender filters
        # Pattern: "with gender male" or "gender is female"
        gender_pattern1 = r'(?:with|has)\s+gender\s+(\w+)(?!\s*,)'
        gender_pattern2 = r'gender\s+(?:is|=)\s+(\w+)(?!\s*,)'

        gender_match1 = re.search(gender_pattern1, query, re.IGNORECASE)
        gender_match2 = re.search(gender_pattern2, query, re.IGNORECASE)

        if (gender_match1 or gender_match2) and "gender" in self.SCHEMA[table]['columns']:
            # Check if there's a comma nearby (IN operator case)
            match_obj = gender_match1 if gender_match1 else gender_match2
            if match_obj and ',' not in query[match_obj.start():min(len(query), match_obj.end() + 20)]:
                gender_value = gender_match1.group(1) if gender_match1 else gender_match2.group(1)
                conditions.append({
                    "column": "gender",
                    "operator": "=",
                    "value": gender_value,
                    "type": "string"
                })
                confidence = 85.0

        # Extract boolean filters for "in stock", "in_stock", "is active", etc.
        # Pattern: "products in stock" → in_stock = true
        if "in_stock" in self.SCHEMA[table].get('boolean_columns', []):
            if re.search(r'\bin\s+stock\b', query, re.IGNORECASE):
                conditions.append({
                    "column": "in_stock",
                    "operator": "=",
                    "value": "true",
                    "type": "boolean"
                })
                confidence = 90.0

        # Extract customer_id filter: "for customer X" or "customer X"
        if "customer_id" in self.SCHEMA[table]['columns']:
            customer_pattern1 = r'(?:for|from)\s+customer\s+(\d+)'
            customer_pattern2 = r'customer\s+(\d+)'
            match = re.search(customer_pattern1, query, re.IGNORECASE)
            if not match:
                match = re.search(customer_pattern2, query, re.IGNORECASE)
            if match:
                conditions.append({
                    "column": "customer_id",
                    "operator": "=",
                    "value": match.group(1),
                    "type": "numeric"
                })
                confidence = 90.0

        # Extract LIKE operator patterns
        # Use case-insensitive matching but preserve captured value case
        for col in self.SCHEMA[table]['columns']:
            like_patterns = [
                rf'{col}\s+like\s+["\']?(\w+)["\']?',
                rf'{col}\s+containing\s+(\w+)',
                rf'with\s+{col}\s+like\s+(\w+)',
            ]
            for pattern in like_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    # Preserve case in the captured value
                    conditions.append({
                        "column": col,
                        "operator": "LIKE",
                        "value": f"%{match.group(1)}%",
                        "type": "like"
                    })
                    confidence = 85.0
                    break

        # Extract IN operator (multiple values only)
        # Use case-insensitive matching but preserve captured value case
        # IMPORTANT: Check this BEFORE single-value patterns
        for col in self.SCHEMA[table]['columns']:
            # Pattern: "year in 2023, 2024" or "in year 2023, 2024" or "in department IT, HR"
            # Match both numbers and words (for string columns)
            in_patterns = [
                rf'{col}\s+in\s+([\w,\s]+)',  # "year in 2023, 2024" or "status in pending, shipped"
                rf'(?:in|with)\s+{col}\s+([\w,\s]+)',  # "in year 2023, 2024" or "with status pending, shipped"
            ]
            for pattern in in_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    values_str = match.group(1)
                    # Only proceed if there's actually a comma (multiple values)
                    if ',' in values_str:
                        values = [v.strip() for v in values_str.split(',')]
                        # Check if NOT IN
                        is_not = bool(re.search(rf'not\s+(?:in|with)\s+{col}', query, re.IGNORECASE))
                        conditions.append({
                            "column": col,
                            "operator": "NOT IN" if is_not else "IN",
                            "value": values,
                            "type": "string" if col in self.SCHEMA[table].get('string_columns', []) else "numeric"
                        })
                        confidence = 90.0
                        break

        return {"conditions": conditions, "confidence": confidence}

    def _extract_calculations(self, query: str, table: Optional[str]) -> Dict:
        """Extract arithmetic calculations (e.g., salary + bonus)"""
        if not table or table not in self.SCHEMA:
            return {"has_calculation": False, "expression": None, "columns": []}

        # Operator keywords mapping
        operators = {
            '+': ['plus', 'add', 'added', 'sum'],
            '-': ['minus', 'subtract', 'less'],
            '*': ['times', 'multiply', 'multiplied'],
            '/': ['divide', 'divided']
        }

        # Check if query has calculation keywords
        has_calc_keyword = False
        found_operator = None
        for op_symbol, keywords in operators.items():
            if any(kw in query for kw in keywords):
                has_calc_keyword = True
                found_operator = op_symbol
                break

        if not has_calc_keyword:
            return {"has_calculation": False, "expression": None, "columns": []}

        # Find columns involved in calculation
        # Check for full column names, partial matches, and synonyms
        mentioned_cols = []
        query_words = query.split()

        for col in self.SCHEMA[table].get('numeric_columns', []):
            # Strategy 1: Exact match (with or without underscores)
            if col in query or col.replace('_', ' ') in query:
                mentioned_cols.append(col)
                continue

            # Strategy 2: Partial match (e.g., "discount" matches "discount_amount")
            # Match if first part of column name is in query
            col_parts = col.split('_')
            if col_parts[0] in query_words and len(col_parts[0]) > 3:
                # Make sure we don't match "price" to both "price" and "cost_price"
                # Only match if the first part is the main identifier
                mentioned_cols.append(col)
                continue

            # Strategy 3: Check synonyms
            for syn in self.COLUMN_SYNONYMS.get(col, []):
                if syn in query:
                    mentioned_cols.append(col)
                    break

        # Remove duplicates while preserving order
        mentioned_cols = list(dict.fromkeys(mentioned_cols))

        # If we matched more than 2 columns, try to pick the most relevant
        # by preferring columns whose first part exactly matches a query word
        if len(mentioned_cols) > 2:
            # Prioritize columns whose first part is an exact word match
            priority_cols = []
            for col in mentioned_cols:
                col_first_part = col.split('_')[0]
                if col_first_part in query_words:
                    priority_cols.append(col)
            if len(priority_cols) >= 2:
                mentioned_cols = priority_cols[:2]

        # Need at least 2 columns for calculation
        if len(mentioned_cols) >= 2:
            col1, col2 = mentioned_cols[0], mentioned_cols[1]
            return {
                "has_calculation": True,
                "expression": f"{col1} {found_operator} {col2}",
                "columns": [col1, col2]
            }

        return {"has_calculation": False, "expression": None, "columns": []}

    RELATIONSHIPS = {
        ("orders", "customers"): ("customer_id", "id"),
        ("orders", "products"): ("product_id", "id"),
        ("employees", "departments"): ("department", "department_name"),
        ("projects", "departments"): ("department_id", "id")
    }

    def extract_join(self, query, detected_tables):
        if len(detected_tables) < 2:
            return None

        # Simple logic: check if any pair of detected tables has a defined relationship
        for (t1, t2), (col1, col2) in self.RELATIONSHIPS.items():
            if t1 in detected_tables and t2 in detected_tables:
                return {
                    "type": "INNER JOIN",
                    "left_table": t1,
                    "right_table": t2,
                    "on": f"{t1}.{col1} = {t2}.{col2}"
                }
        return None

    def _determine_intent(self, agg_info: Dict, rank_info: Dict, filter_info: Dict, calc_info: Dict = None) -> str:
        """Determine the primary intent of the query"""
        # CRITICAL: Prioritize calculation if found
        if calc_info and calc_info.get('has_calculation'):
            return 'calculation'

        # CRITICAL: If we have ranking direction AND limit, prioritize ranking over aggregation
        # Example: "Find 4 suppliers with lowest delivery time" should be ranking, not MIN aggregation
        if rank_info['direction'] and rank_info['limit']:
            return "ranking"
        # If we have aggregation function but NO limit, it's aggregation
        elif agg_info['function']:
            return "aggregation"
        elif filter_info['conditions']:
            return "filtering"
        else:
            return "retrieval"

    def get_numeric_columns(self, table: str) -> List[str]:
        """Get list of numeric columns for a table"""
        if table in self.SCHEMA:
            return self.SCHEMA[table]['numeric_columns']
        return []

    def validate_column(self, table: str, column: str) -> bool:
        """Check if column exists in table"""
        if table in self.SCHEMA:
            return column in self.SCHEMA[table]['columns']
        return False