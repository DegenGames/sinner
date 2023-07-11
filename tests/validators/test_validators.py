from argparse import Namespace

from sinner.Parameters import Parameters
from tests.validators.TestValidatedClass import DEFAULT_VALUE, TestDefaultValidation, TestRequiredValidation, TestUntypedAttribute, TestEqualValueAttribute, TestInValueAttribute, TestLambdaValueAttribute, TestInitAttribute, TestListAttribute


def test_default_validator() -> None:
    parameters: Namespace = Parameters.command_line_to_namespace('')
    test_object = TestDefaultValidation()

    assert test_object.default_parameter is None
    assert test_object.parameter_name is None

    assert test_object.load(parameters) is True
    assert test_object.default_parameter == DEFAULT_VALUE
    assert test_object.parameter_name == DEFAULT_VALUE
    assert test_object.errors == []

    # test if default validator doesn't overwrite existing values
    test_object.default_parameter = 14
    test_object.parameter_name = 88
    assert test_object.load(parameters) is True
    assert test_object.default_parameter == 14
    assert test_object.parameter_name == 88
    assert test_object.errors == []


def test_required_validator() -> None:
    parameters: Namespace = Parameters.command_line_to_namespace('')
    test_object = TestRequiredValidation()
    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    # assert test_object.required_default_parameter is None

    # nothing should be changed, if loading unsuccessful
    assert test_object.load(parameters) is False
    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    assert test_object.required_default_parameter is None
    assert test_object.errors != []

    # ignore validation on load
    assert test_object.load(attributes=parameters, validate=False) is True

    assert test_object.required_parameter is None
    assert test_object.default_required_parameter is None
    assert test_object.required_default_parameter is None

    parameters = Parameters.command_line_to_namespace('--required-parameter=test')
    assert test_object.load(attributes=parameters) is True
    assert test_object.required_parameter == 'test'
    assert test_object.default_required_parameter == DEFAULT_VALUE
    assert test_object.required_default_parameter == DEFAULT_VALUE

    #  trying to use integer value
    parameters = Parameters.command_line_to_namespace('--required-parameter=test --default_required_parameter=100')
    assert test_object.load(attributes=parameters) is True
    assert test_object.required_parameter == 'test'
    assert test_object.default_required_parameter == 100
    assert test_object.required_default_parameter == DEFAULT_VALUE


def test_untyped_attribute() -> None:
    test_object = TestUntypedAttribute()
    parameters: Namespace = Parameters.command_line_to_namespace('--untyped-attribute=value')
    assert test_object.load(attributes=parameters) is True
    assert test_object.untyped_attribute == 'value'


def test_equal_value_validator() -> None:
    test_object = TestEqualValueAttribute()
    assert test_object.int_attribute is None
    parameters: Namespace = Parameters.command_line_to_namespace('--int_attribute=10')
    assert test_object.load(attributes=parameters) is True
    assert test_object.int_attribute == 10

    parameters: Namespace = Parameters.command_line_to_namespace('--int_attribute=42')
    assert test_object.load(attributes=parameters) is False
    assert test_object.int_attribute == 10
    assert test_object.errors == [{'attribute': 'int_attribute', 'error': 'Value 42 is not equal to 10', 'module': 'TestEqualValueAttribute'}]


def test_in_value_validator() -> None:
    test_object = TestInValueAttribute()
    assert test_object.in_list_attribute is None
    parameters: Namespace = Parameters.command_line_to_namespace('--in_list_attribute=7')
    assert test_object.load(attributes=parameters) is True
    assert test_object.in_list_attribute == 7

    parameters: Namespace = Parameters.command_line_to_namespace('--in_list_attribute=42')
    assert test_object.load(attributes=parameters) is True
    assert test_object.in_list_attribute == 42

    parameters: Namespace = Parameters.command_line_to_namespace('--in_list_attribute=15')
    assert test_object.load(attributes=parameters) is False
    assert test_object.in_list_attribute == 42


def test_lambda_validator() -> None:
    test_object = TestLambdaValueAttribute()
    assert test_object.lambda_attribute is None
    parameters: Namespace = Parameters.command_line_to_namespace('--lambda_attribute=7')
    assert test_object.load(attributes=parameters) is False
    assert test_object.lambda_attribute is None

    parameters: Namespace = Parameters.command_line_to_namespace('--lambda_attribute=42')
    assert test_object.load(attributes=parameters) is True
    assert test_object.lambda_attribute == 42

    parameters: Namespace = Parameters.command_line_to_namespace('--lambda_attribute=15')
    assert test_object.load(attributes=parameters) is False
    assert test_object.lambda_attribute == 42


def test_list_parameter() -> None:
    test_object = TestListAttribute()
    assert test_object.list_attribute is None
    parameters: Namespace = Parameters.command_line_to_namespace('')
    assert test_object.load(attributes=parameters) is True
    assert test_object.list_attribute == ['Dolor', 'sit', 'amet']

    parameters: Namespace = Parameters.command_line_to_namespace('--list_attribute Ipsum lorem')
    assert test_object.load(attributes=parameters) is True
    assert test_object.list_attribute == ['Ipsum', 'lorem']

    parameters: Namespace = Parameters.command_line_to_namespace('--list_attribute=42')
    assert test_object.load(attributes=parameters) is True
    assert test_object.list_attribute == ['42']

    parameters: Namespace = Parameters.command_line_to_namespace('--list_attribute --other-attribute')  # parameter without values validates to True
    assert test_object.load(attributes=parameters) is True
    assert test_object.list_attribute == [True]
