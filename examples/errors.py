import sys
from colors import c
from bdsl_types import InterpreterContext


# class CLIError(Exception):


class InterpreterError(Exception):
    '''Generic error for the bdsl interpreter.'''

    def __init__(self,
                 message: str,
                 lineno: int,
                 interpreter_context: InterpreterContext | None = None,
                 cols: tuple[int, int] | None = None,
                 ) -> None:
        '''Initialize the error.

        Args:
            message: The error message.
            lineno: The line number where the error occurred.
            program_data: The ProgramData where the error occurred(optional).
            cols: The colums number where the error occurred(optional).
        '''
        self.lineno = lineno
        self.cols = cols
        self.filename = interpreter_context

        numcol = c.MAGENTA.get_text

        # Format the error message with location information
        location = ''
        if interpreter_context is not None:
            location += f"at {numcol(interpreter_context.program_data.filename)}, "
        location += f"line {numcol(lineno)}"
        if cols is not None:
            location += f", column {numcol(cols[0])}"

        full_message = f"{message} ({location})"

        sys.exit(full_message)


class VarMessageException(InterpreterError):
    '''
    Base class for exceptions related to a variable.

    By default the error prints:
        "{__class__.__name__}: {varname} (at {location})"
    '''

    def __init__(self,
                 varname: str,
                 lineno: int,
                 interpreter_context: InterpreterContext | None = None,
                 colno: int | None = None,
                 ) -> None:
        message = self.get_message_format().format(varname=varname)

        if colno:
            cols = (colno, colno+len(varname))
        else:
            cols = None
        super().__init__(message, lineno, interpreter_context, cols)

    def get_message_format(self):
        return f'{c.FAIL.get_text(self.__class__.__name__)}: {c.CYAN.get_text('{varname}')}'


class VariableNotDefinedError(VarMessageException):
    '''The given variable is not defined'''

    # def get_message_format(self):
    #     return 'VariableNotDefined: {varname}'


class VariableWithoutBoundsError(VarMessageException):
    '''The given variable has no bounds'''

    # def get_message_format(self):
    #     return 'VariableWithoutBounds: {varname}'
