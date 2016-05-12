from copy import deepcopy
from subprocess import Popen
from re import compile
from types import SimpleNamespace

import pandas as pd
from scipy.stats import chi2


__all__ = ['Model', 'lr_test']

# Valid model types
MODEL_TYPES = ['BP', 'CNL', 'MNL', 'NGEV', 'NL', 'OL']

# Fields to read from the .rep file, for Model.read_results()
#   label : (name, converter)
STATS = {
    'Final log likelihood': ('LB', float),
    'Number of estimated parameters': ('k', int),
    'Rho-square': ('p2', float),
    'Adjusted rho-square': ('p2_adj', float),
    }

# Regular expressions for lines in .mod and .res files, for Model._read_mod()
REGEX = {
    'Beta': '(\w+)\s+' + '([-+\d.eE]+)\s+' * 3 + '([01])',
    'Expressions': '(?P<name>.*?)\s*?=\s*(?P<expr>.*)',
    'Utilities': '(\w+)\s+' * 3 + '(.*)',
    }
REGEX = {key: compile(expr) for key, expr in REGEX.items()}

# Unsupported sections of .mod and .res files, for Model._read_mod()
SKIP = [
    # These sections contain only "$NONE" in the .res file. Omitting them from
    # biosim does not affect simulation results
    'AggregateLast',
    'AggregateWeight',
    'CNLAlpha',
    'CNLNests',
    'Exclude',
    'GeneralizedUtilities',
    'IIATest',
    'LaTeX',
    'LinearConstraints',
    'NetworkGEVLinks',
    'NetworkGEVNodes',
    'NLNests',
    'NonLinearEqualityConstraints',
    'NonLinearInequalityConstraints',
    'OrdinalLogit',
    'PanelData',
    'ParameterCovariances',
    'Ratios',
    'SelectionBias',
    'SNP',
    'Weight',
    'ZhengFosgerau',
    # These sections contain data in the .res file but, unless their defaults
    # are overridden in the .mod file, omitting them from biosim does not
    # affect simulation results
    'Draws',  # 150
    'Group',  # 1
    'Mu',  # 1 0 1 1 (same fields as Beta: value, lower, upper, status)
    'SampleEnum',  # 0
    'Scale',  # 1 1 1 1 1 (group #, scale, lower, upper, status)
    ]


def fn(model, ext):
    """Determine model file name."""
    if model.name is None:
        raise ValueError('Unable to determine name of %s.' % model)
    return str(model.name) + '.' + ext


class Model:
    """Simple class for a Biogeme model."""
    name = None  # A name for the model
    stats = None  # Statistics of the estimated model
    _available = {}  # choice alternative : availability variable
    _expressions = {}  # name : expression string

    def __init__(self, data_fn=None, model_type='MNL',
                 choice=None, avail_vars='avail%d', name=None, load=False):
        """Initialize a model with empty utility functions.

        Biogeme-compatible data in *data_filename* is read for the list of
        variables. *model_type* must be one of the valid Biogeme model types.
        *choice* indicates the variable containing the alternative selection.
        *name* is an optional name for the model.

        *avail_vars* is a format string for the variables containing
        availability information for each alternative. For instance, if column
        *choice* in *data_filename* contains the integers 3, 5 and 8; and
        *avail_vars* is "has%d", then the variables "has3", "has5", and "has8"
        will tbe the availability indicator variables for alternatives 3, 5 and
        8 respectively.

        Errors are raised on missing variables.

        """
        self.name = name
        self.stats = SimpleNamespace()

        # Read the list of variables
        self._data_fn = data_fn
        self.data = pd.read_table(data_fn)
        self._variables = self.data.columns.tolist()

        # Coefficients
        self._beta = pd.DataFrame(columns=['value', 'lower', 'upper', 'fixed'])

        if load:
            self.read_results(overwrite=True)
        else:
            # Initialize a blank model

            # Set the model type and choice variable
            self.model_type = model_type
            self.choice = choice

            # Check for the availability variables, and save their names
            for c in self.choices:
                self.set_avail(c, avail_vars % c)

    @property
    def model_type(self):
        return self._model_type

    @model_type.setter
    def model_type(self, value):
        assert value in MODEL_TYPES
        self._model_type = value

    @property
    def choice(self):
        return self._choice

    @choice.setter
    def choice(self, value):
        # Check for the choice variable
        if value not in self._variables:
            raise ValueError("Choice variable '{}' is not among: {}"
                             .format(value, self._variables))
        elif hasattr(self, 'D'):
            raise ValueError('Trying to change choice variable on a model'
                             'with a design matrix.')
        # Record the choice variable and its distinct values
        self._choice = value
        self.choices = sorted(self.data[value].unique())
        self.D = pd.Panel(items=self.choices, minor_axis=self._variables,
                          dtype=bool)

    def add_as(self, name_template, var_template):
        """Add alternative-specific coefficients to the model.

        The coefficient names are constructed using *name_template*, and the
        alternative-specific information is located in variables with names
        constructed using *var_template*.

        """
        for c in self.choices:
            name = name_template % c
            var = var_template % c
            assert var in self._variables, \
                ("Variable '{}' for alternative-specific coefficient '{}' not "
                 "found").format(var, name)
            self.add_beta(name)
            self.D.loc[c, name, var] = True

    def add_asconst(self, name_template='ASC%s', fixed='first'):
        """Add alternative-specific constants (ASC) to the model.

        A constant is added to the model, if one does not already exist.
        add_asconst() passes *name_template* and *fixed* to add_attribute().

        """
        # Add a constant to the model
        if 1 not in self._expressions.values():
            self.add_expression('one', 1)
            const = 'one'
        else:
            # A constant already exists; determine its name
            for key, value in self._expressions.items():
                if value == 1:
                    const = key
        # Iterate over alternatives
        self.add_attribute(name_template, const, fixed)

    def add_beta(self, name, value=0, lower=-100, upper=100, fixed=False):
        """Add a coefficient to the model."""
        data = pd.Series(dict(value=value, lower=lower, upper=upper,
                              fixed=fixed), name=name)
        if name in self._beta.index:
            # The coefficient already exists; replace its values
            self._beta.loc[name, :] = data
        else:
            # Add the coefficient
            self._beta = self._beta.append(data)
            # Extend the design matrix to include the new coefficient
            self.D = self.D.reindex_axis(self._beta.index, axis=1)

    def remove_beta(self, name):
        """Remove a coefficient from the model."""
        self._beta.drop(name, inplace=True)
        self.D.drop(name, axis=1, inplace=True)

    def add_expression(self, name, value):
        """Add an expression."""
        assert name not in self._variables, \
            "Expression name '{}' clashes with existing variable".format(name)
        self._expressions[name] = value
        # Extend the design matrix to include the new expression
        self._variables.append(name)
        self.D = self.D.reindex_axis(self._variables, axis=2)

    def add_generic(self, name, var_template):
        """Add a generic coefficient, *name*, to the model.

        The alternative-specific information is located in variables with names
        constructed using *var_template*.

        """
        self.add_beta(name)
        for c in self.choices:
            var = var_template % c
            assert var in self._variables, \
                ("Variable '{}' for generic coefficient '{}' not found") \
                .format(var, name)
            self.D.loc[c, name, var] = True

    def add_attribute(self, name_template, var, fixed='first'):
        """Add alternative-specific coefficients for individuals' attributes.

        One of the coefficients is fixed to 0; *fixed* indicates which
        (currently the only supported value is 'first', meaning the lowest
        unique value of the choice variable). The names of the constants are
        constructed using *name_template*.

        """
        assert fixed == 'first' or fixed in self.choices
        # Iterate over alternatives
        for i, c in enumerate(self.choices):
            name = name_template % c
            # Add the coefficient
            self.add_beta(name, fixed=((fixed == 'first' and i == 0) or
                                       (fixed == c)))
            # Coefficient times the attribute in the design matrix
            self.D.loc[c, name, var] = True

    def copy(self, name=None, data_fn=None):
        result = deepcopy(self)
        if name is not None:
            result.name = name
        if data_fn is not None:
            result._data_fn = data_fn
        return result

    def estimate(self, name=None):
        """Run the model.

        If *name* is given, the model is stored in "*name*.mod", and full
        results are stored in "*name*.rep" and "*name*.res"; if *name* is None
        (default), the name attribute of the Model is used; and if neither is
        given, a ValueError is raised.

        """
        self._run('biogeme')
        self.read_results()

    def read_results(self, overwrite=False):
        """Read model estimates from *basename*.rep and *basename*.res."""
        # .rep file
        with open(fn(self, 'rep')) as f:
            for line in f:
                for label, var in STATS.items():
                    if label in line:
                        name, conv = var
                        setattr(self.stats, name, conv(line.split(':')[1]))
                        continue
        # .res file
        with open(fn(self, 'res')) as f:
            self._read_mod(f, beta_only=not overwrite)

    def _read_mod(self, f, beta_only=False):
        """Read model from a .mod or .res file object *f*."""
        section = None
        skip = False
        groups = {section: [] for section in REGEX.keys()}
        for line in f:
            # Strip comments
            line = line.split('//')[0].strip()

            # Start of a new section
            if line.startswith('['):
                section = line.strip('[]')
                skip = (section in SKIP or (beta_only and section != 'Beta'))
                continue

            # Skip empty lines or unsupported sections
            if len(line) == 0 or skip:
                continue
            elif section == 'Choice':
                self.choice = line
                continue
            elif section == 'Model':
                self.model_type = line.lstrip('$')
                continue

            # Parse line using a regular expression
            match = REGEX[section].match(line)
            if match is None:
                raise ValueError("could not parse '{}' in section '{}'"
                                 .format(line, section))
            else:
                # Cache the matched values, so they can be loaded in order
                groups[section].append(match.groups())
        for g in groups['Beta']:
            name = g[0].strip()
            value, lower, upper = map(float, g[1:4])
            fixed = bool(int(g[4]))
            self.add_beta(name, value, lower, upper, fixed)
        for g in groups['Expressions']:
            name, expr = map(lambda x: x.strip(), g)
            self.add_expression(name, expr)
        for g in groups['Utilities']:
            id = type(self.choices[0])(g[0])
            self.set_avail(id, g[2])
            # Parse the utility expression
            for term in g[3].split(' + '):
                beta, variable = term.split(' * ')
                assert beta in self._beta.index, \
                    "coefficient '{}' not found".format(beta)
                assert variable in self._variables, \
                    "variable '{}' not found".format(variable)
                # Update the design matrix
                self.D.loc[id, beta, variable] = True

    def _run(self, program):
        """Common code for estimate() and simulate()."""
        # Determine model file name
        model_fn = fn(self, 'mod')
        self.write(model_fn)
        p = Popen([program + '.sh', model_fn, self._data_fn])
        p.wait()

    def simulate(self):
        """Simulate choice probabilities.

        If *name* is given, the model is stored in "*name*.mod", and full
        results are stored in "*name*.enu"; if *name* is None (default), the
        name attribute of the Model is used; and if neither is given, a
        ValueError is raised.

        """
        self._run('biosim')
        tmp = pd.read_table(fn(self, 'enu'))
        assert (len(self.data.index) == len(tmp.index) and
                all(self.data[self.choice] == tmp['Choice_Id']))
        # Split the simulated results into separate variables
        col_groups = {
            'P': 'P_Alt{}',
            'resid': 'Residual_Alt{}',
            'V': 'V_Alt{}',
            }
        for var, names in col_groups.items():
            # Names of columns in the .enu file : choice id
            cols = {names.format(c): c for c in self.choices}
            # Select the columns, then rename them from 'P_Alt1' → 1
            setattr(self, var, tmp[list(cols.keys())].rename(columns=cols))

    def set_avail(self, alternative, variable):
        """Set the availability *variable* for choice *alternative*."""
        assert variable in self._variables, \
            'Availability variable for {}={}, {}, not found.'.format(
                                            self.choice, alternative, variable)
        self._available[alternative] = variable

    def write(self, filename):
        """Write the model to *filename*."""
        with open(filename, 'w') as f:
            def section(name, first=False):
                if not first:
                    f.write('\n')
                f.write('[{}]\n'.format(name))

            section('Model', first=True)
            f.write('$%s' % self.model_type)

            section('Choice')
            f.write('%s\n' % self.choice)

            section('Expressions')
            for name, expr in sorted(self._expressions.items()):
                f.write('{} = {}\n'.format(name, expr))

            section('Beta')
            f.write('//')  # Comment the header row of the table
            # Write the 'fixed' column as '1'/'0', instead of 'True'/'False'
            self._beta.to_string(f, formatters={'fixed': lambda v: '%d' % v})

            section('Utilities')
            for c in self.choices:
                entries = [str(c), 'Alt%d' % c, self._available[c], '']
                for var, betas in self.D.loc[c, :, :].iteritems():
                    if not betas.any():
                        continue
                    betas = betas[betas == True].index.tolist()  # NOQA
                    assert len(betas) == 1
                    entries[-1] += '{} * {} + '.format(betas[0], var)
                entries[-1] = entries[-1][:-3]
                f.write('  '.join(entries) + '\n')

    def write_data(self, **kwargs):
        self.data.to_csv(self._data_fn, index=False, sep='\t', **kwargs)


def lr_test(u, r, alpha=0.05):
    """Perform a likelihood ratio test.

    *u* and *r* are unrestricted and restricted Models, respectively.

    """
    u = u.stats
    r = r.stats
    X = -2 * (r.LB - u.LB)
    X_crit = chi2.ppf(1 - alpha, df=u.k - r.k)
    print(("-2 ({} + {}) = {:.1f} > {:.1f} = "
           "\\mathcal{{X}}^2_{{(0.95, {} - {})}} : \\text{{{}}}").format(
          r.LB, -u.LB, X, X_crit, u.k, r.k, X > X_crit))
