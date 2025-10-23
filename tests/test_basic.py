"""
Tests básicos que funcionan sin dependencias externas
"""

import pytest


class TestBasic:
    """Tests básicos para verificar que pytest funciona"""

    def test_basic_math(self):
        """Test básico de matemáticas"""
        assert 2 + 2 == 4
        assert 3 * 3 == 9
        assert 10 / 2 == 5

    def test_string_operations(self):
        """Test básico de strings"""
        text = "Hello World"
        assert len(text) == 11
        assert "Hello" in text
        assert text.upper() == "HELLO WORLD"

    def test_list_operations(self):
        """Test básico de listas"""
        numbers = [1, 2, 3, 4, 5]
        assert len(numbers) == 5
        assert 3 in numbers
        assert max(numbers) == 5
        assert min(numbers) == 1

    def test_dict_operations(self):
        """Test básico de diccionarios"""
        data = {"name": "test", "value": 42}
        assert "name" in data
        assert data["name"] == "test"
        assert data["value"] == 42

    def test_boolean_operations(self):
        """Test básico de booleanos"""
        assert True is True
        assert False is False
        assert not False is True
        assert True and True is True
        assert True or False is True
