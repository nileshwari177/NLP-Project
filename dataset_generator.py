"""
Dataset Generator for NLP to SQL System
Generates additional test cases using templates and variations
"""

import json
import random
from typing import Dict, List, Any
from interactive_nlp_extractor import NLPExtractor


class DatasetGenerator:
    """Generate synthetic test cases for NLP to SQL"""

    def __init__(self):
        """Initialize with schema information"""
        self.extractor = NLPExtractor()
        self.schema = self.extractor.SCHEMA

        # Templates for different query types
        self.templates = {
            'basic_retrieval': [
                ("Show all {table_alias}", "SELECT * FROM {table};"),
                ("Display all {table_alias}", "SELECT * FROM {table};"),
                ("List all {table_alias}", "SELECT * FROM {table};"),
                ("Get all {table_alias}", "SELECT * FROM {table};"),
                ("Show {column}", "SELECT {column} FROM {table};"),
                ("Get {column} from {table_alias}", "SELECT {column} FROM {table};"),
                ("Display {column} of {table_alias}", "SELECT {column} FROM {table};"),
            ],
            'aggregation': [
                ("What is the average {column} of {table_alias}", "SELECT AVG({column}) as result FROM {table};"),
                ("Calculate average {column}", "SELECT AVG({column}) as result FROM {table};"),
                ("Find mean {column} in {table}", "SELECT AVG({column}) as result FROM {table};"),
                ("Calculate total {column}", "SELECT SUM({column}) as result FROM {table};"),
                ("What is the sum of {column}", "SELECT SUM({column}) as result FROM {table};"),
                ("Count how many {table_alias}", "SELECT COUNT(id) as result FROM {table};"),
                ("How many {table_alias} are there", "SELECT COUNT(id) as result FROM {table};"),
                ("Find maximum {column}", "SELECT MAX({column}) as result FROM {table};"),
                ("What is the highest {column}", "SELECT MAX({column}) as result FROM {table};"),
                ("Find minimum {column}", "SELECT MIN({column}) as result FROM {table};"),
                ("What is the lowest {column}", "SELECT MIN({column}) as result FROM {table};"),
            ],
            'ranking': [
                ("Show top {limit} {table_alias} with highest {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} DESC LIMIT {limit};"),
                ("Get top {limit} {table_alias} by {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} DESC LIMIT {limit};"),
                ("Find {limit} {table_alias} with best {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} DESC LIMIT {limit};"),
                ("Show bottom {limit} {table_alias} with lowest {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} ASC LIMIT {limit};"),
                ("Get {limit} worst {table_alias} by {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} ASC LIMIT {limit};"),
                ("Top {limit} {table_alias} sorted by {column}",
                 "SELECT id, {column} FROM {table} ORDER BY {column} DESC LIMIT {limit};"),
            ],
            'filtering': [
                ("{table_alias} with {column} greater than {value}",
                 "SELECT * FROM {table} WHERE {column} > {value};"),
                ("Show {table_alias} where {column} is above {value}",
                 "SELECT * FROM {table} WHERE {column} > {value};"),
                ("Find {table_alias} with {column} less than {value}",
                 "SELECT * FROM {table} WHERE {column} < {value};"),
                ("{table_alias} where {column} below {value}",
                 "SELECT * FROM {table} WHERE {column} < {value};"),
                ("Get {table_alias} in {filter_column} {filter_value}",
                 "SELECT * FROM {table} WHERE {filter_column} = '{filter_value}';"),
                ("{table_alias} from {filter_column} {filter_value}",
                 "SELECT * FROM {table} WHERE {filter_column} = '{filter_value}';"),
            ],
            'complex_filtering_aggregation': [
                ("Average {column} of {table_alias} in {filter_column} {filter_value}",
                 "SELECT AVG({column}) as result FROM {table} WHERE {filter_column} = '{filter_value}';"),
                ("Total {column} of {table_alias} where {filter_column} is {filter_value}",
                 "SELECT SUM({column}) as result FROM {table} WHERE {filter_column} = '{filter_value}';"),
                ("Count {table_alias} with {num_column} greater than {value}",
                 "SELECT COUNT(id) as result FROM {table} WHERE {num_column} > {value};"),
                ("Maximum {column} in {filter_column} {filter_value}",
                 "SELECT MAX({column}) as result FROM {table} WHERE {filter_column} = '{filter_value}';"),
            ],
            'complex_filtering_ranking': [
                ("Top {limit} {table_alias} with highest {column} in {filter_column} {filter_value}",
                 "SELECT id, {column} FROM {table} WHERE {filter_column} = '{filter_value}' ORDER BY {column} DESC LIMIT {limit};"),
                ("Best {limit} {table_alias} by {column} from {filter_column} {filter_value}",
                 "SELECT id, {column} FROM {table} WHERE {filter_column} = '{filter_value}' ORDER BY {column} DESC LIMIT {limit};"),
                ("Bottom {limit} {table_alias} with lowest {column} where {filter_column} is {filter_value}",
                 "SELECT id, {column} FROM {table} WHERE {filter_column} = '{filter_value}' ORDER BY {column} ASC LIMIT {limit};"),
            ]
        }

        # Value ranges for numeric filters
        self.value_ranges = {
            'marks': (50, 100, 10),
            'cgpa': (2.0, 4.0, 0.5),
            'salary': (30000, 100000, 10000),
            'price': (10000, 100000, 10000),
            'age': (18, 30, 2),
            'rating': (3.0, 5.0, 0.5),
            'year': (2020, 2024, 1),
            'experience_years': (1, 10, 2),
            'mileage': (10, 25, 5),
        }

        # String filter options
        self.string_filters = {
            'department': ['Engineering', 'IT', 'Sales', 'Marketing', 'HR'],
            'category': ['Electronics', 'Clothing', 'Books', 'Food', 'Sports'],
            'city': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune'],
            'major': ['Computer Science', 'Electrical', 'Mechanical', 'Civil'],
            'brand': ['Toyota', 'Honda', 'Ford', 'BMW', 'Tesla'],
        }

    def generate_samples(self, num_samples: int = 100) -> List[Dict[str, Any]]:
        """
        Generate synthetic test samples

        Args:
            num_samples: Number of samples to generate

        Returns:
            List of test case dictionaries
        """
        samples = []
        sample_id = 1

        # Calculate samples per category
        categories = list(self.templates.keys())
        samples_per_category = num_samples // len(categories)

        for category in categories:
            for _ in range(samples_per_category):
                sample = self._generate_sample(category, sample_id)
                if sample:
                    samples.append(sample)
                    sample_id += 1

        return samples

    def _generate_sample(self, category: str, sample_id: int) -> Dict[str, Any]:
        """Generate a single sample for a given category"""
        templates = self.templates.get(category, [])
        if not templates:
            return None

        # Pick random template
        nl_template, sql_template = random.choice(templates)

        # Pick random table
        table = random.choice(list(self.schema.keys()))
        table_info = self.schema[table]
        table_alias = random.choice(table_info['aliases'])

        # Initialize variables
        variables = {
            'table': table,
            'table_alias': table_alias,
        }

        # Category-specific variable selection
        if category in ['aggregation', 'ranking', 'complex_filtering_aggregation', 'complex_filtering_ranking']:
            # Need numeric column
            if table_info['numeric_columns']:
                column = random.choice(table_info['numeric_columns'])
                variables['column'] = column
            else:
                return None

        elif category in ['basic_retrieval']:
            # Could be any column or *
            if random.random() > 0.5 and table_info['columns']:
                column = random.choice(table_info['columns'][:5])  # Pick from first few columns
                variables['column'] = column
            else:
                return None  # Skip this one, we want column-specific ones

        elif category in ['filtering', 'complex_filtering_aggregation', 'complex_filtering_ranking']:
            # Need numeric column for comparison
            if table_info['numeric_columns']:
                num_column = random.choice(table_info['numeric_columns'])
                variables['column'] = num_column
                variables['num_column'] = num_column

                # Generate value based on column
                value = self._generate_value(num_column)
                variables['value'] = value
            else:
                return None

        # Add limit for ranking queries
        if category in ['ranking', 'complex_filtering_ranking']:
            variables['limit'] = random.choice([3, 5, 7, 10, 15, 20])

        # Add string filters for complex queries
        if category in ['complex_filtering_aggregation', 'complex_filtering_ranking']:
            # Find a suitable string column for filtering
            filter_column = None
            filter_value = None

            for str_col, values in self.string_filters.items():
                if str_col in table_info['columns']:
                    filter_column = str_col
                    filter_value = random.choice(values)
                    break

            if filter_column:
                variables['filter_column'] = filter_column
                variables['filter_value'] = filter_value
            else:
                # No suitable filter column, skip
                return None

        # Format templates with variables
        try:
            natural_language = nl_template.format(**variables)
            expected_sql = sql_template.format(**variables)
        except KeyError:
            # Missing variable, skip this sample
            return None

        # Determine difficulty
        difficulty = 'easy' if category == 'basic_retrieval' else 'medium'
        if 'complex' in category:
            difficulty = 'hard'

        return {
            'id': sample_id,
            'category': category,
            'natural_language': natural_language,
            'expected_sql': expected_sql,
            'difficulty': difficulty,
            'keywords': variables
        }

    def _generate_value(self, column: str) -> Any:
        """Generate a random value for a numeric column"""
        if column in self.value_ranges:
            min_val, max_val, step = self.value_ranges[column]
            if isinstance(min_val, float):
                return round(random.uniform(min_val, max_val), 1)
            else:
                return random.randrange(min_val, max_val, step)
        else:
            # Default numeric range
            return random.choice([50, 60, 70, 80, 90, 100])

    def save_dataset(self, samples: List[Dict[str, Any]], filename: str):
        """Save generated dataset to JSON file"""
        dataset = {
            'metadata': {
                'description': 'Generated test dataset for NLP to SQL evaluation',
                'version': '1.0',
                'total_samples': len(samples),
                'categories': list(set(s['category'] for s in samples))
            },
            'test_cases': samples
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(samples)} samples to {filename}")

    def extend_existing_dataset(self, existing_file: str, output_file: str, num_new_samples: int = 100):
        """Extend an existing dataset with new generated samples"""
        # Load existing dataset
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

        existing_samples = existing_data.get('test_cases', [])
        next_id = max(s['id'] for s in existing_samples) + 1 if existing_samples else 1

        # Generate new samples
        new_samples = self.generate_samples(num_new_samples)

        # Renumber new samples
        for i, sample in enumerate(new_samples):
            sample['id'] = next_id + i

        # Combine
        all_samples = existing_samples + new_samples

        # Save
        self.save_dataset(all_samples, output_file)

        print(f"📊 Extended dataset: {len(existing_samples)} existing + {len(new_samples)} new = {len(all_samples)} total")


def main():
    """Generate datasets"""
    generator = DatasetGenerator()

    # Generate 100 new samples
    print("🔄 Generating synthetic test samples...")
    samples = generator.generate_samples(num_samples=100)

    # Save to file
    generator.save_dataset(samples, 'generated_test_dataset.json')

    # Show sample breakdown
    category_counts = {}
    for sample in samples:
        cat = sample['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\n📊 Sample breakdown by category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat:40s}: {count:3d} samples")

    # Show some examples
    print("\n📝 Sample examples:")
    for i in range(min(5, len(samples))):
        sample = samples[i]
        print(f"\n  [{sample['id']}] {sample['category']} ({sample['difficulty']})")
        print(f"  NL:  {sample['natural_language']}")
        print(f"  SQL: {sample['expected_sql']}")


if __name__ == "__main__":
    main()
