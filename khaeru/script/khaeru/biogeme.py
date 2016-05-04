from copy import deepcopy
from os.path import basename
import subprocess

import pandas as pd
from scipy.stats import chi2


__all__ = ['Model', 'ModelResults', 'lr_test']


class Model:
    """Simple class for a Biogeme model."""
    __model_types = ['BP', 'CNL', 'MNL', 'NGEV', 'NL', 'OL']

    # Unsupported
    # These sections contain only "$NONE" in the .res file. Omitting them from
    # biosim does not affect simulation results
    __sections = [
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
        ]

    # Unsupported
    # These sections contain data in the .res file but, unless their defaults
    # are overridden in the .mod file, omitting them from biosim does not
    # affect simulation results
    __sections2 = [
        'Draws',  # 150
        'Group',  # 1
        'Mu',  # 1 0 1 1 (same fields as Beta: value, lower, upper, status)
        'SampleEnum',  # 0
        'Scale',  # 1 1 1 1 1 (group #, scale, lower, upper, status)
        ]

    def __init__(self, data_filename=None, model_type='MNL', choice=None,
                 avail_vars='avail%d', name=None):
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

        # Read the list of variables
        self._data_filename = data_filename
        data = pd.read_table(data_filename)
        self._data_columns = data.columns.tolist()

        # Set the model type
        assert model_type in self.__model_types
        self._model_type = model_type

        # Check for the choice variable
        if choice not in self._data_columns:
            raise ValueError("Choice variable '{}' is not among: {}"
                             .format(choice, self._data_columns))

        # Record the choice variable and its distinct values
        self._choice = choice
        self._choices = sorted(data[choice].unique())
        del data  # Not used after this point

        # Check for the availability variables, and save their names
        self._available = {}
        for c in self._choices:
            avail = avail_vars % c
            assert avail in self._data_columns, \
                'Availability variable for {}={}, {}, not found.'.format(
                                                              choice, c, avail)
            self._available[c] = avail

        # Biogeme expressions
        self._expressions = {}

        # Coefficients to be estimated
        self._beta = pd.DataFrame(columns=['value', 'lower', 'upper', 'fixed'])

        # 3-D design matrix for the model, initially empty
        self.D = pd.Panel(items=self._choices, minor_axis=self._data_columns,
                          dtype=bool)

    def add_beta(self, name, value=0, lower=-100, upper=100, fixed=False):
        """Add a coefficient to the model."""
        # Add the coefficient
        self._beta = self._beta.append(pd.Series(dict(value=value,
                                                      lower=lower,
                                                      upper=upper,
                                                      fixed=fixed),
                                                 name=name))
        # Extend the design matrix to include the new coefficient
        self.D = self.D.reindex_axis(self._beta.index, axis=1)

    def remove_beta(self, name):
        """Remove a coefficient from the model."""
        self._beta.drop(name, inplace=True)
        self.D.drop(name, axis=1, inplace=True)

    def add_expression(self, name, value):
        """Add an expression."""
        assert name not in self._data_columns, \
            "Expression name '{}' clashes with existing variable".format(name)
        self._expressions[name] = value
        # Extend the design matrix to include the new expression
        self._data_columns.append(name)
        self.D = self.D.reindex_axis(self._data_columns, axis=2)

    def add_asconst(self, name_template='ASC%d', fixed='first'):
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

    def add_as(self, name_template, var_template):
        """Add alternative-specific coefficients to the model.

        The coefficient names are constructed using *name_template*, and the
        alternative-specific information is located in variables with names
        constructed using *var_template*.

        """
        for c in self._choices:
            name = name_template % c
            var = var_template % c
            assert var in self._data_columns, \
                ("Variable '{}' for alternative-specific coefficient '{}' not "
                 "found").format(var, name)
            self.add_beta(name)
            self.D.loc[c, name, var] = True

    def add_generic(self, name, var_template):
        """Add a generic coefficient, *name*, to the model.

        The alternative-specific information is located in variables with names
        constructed using *var_template*.

        """
        self.add_beta(name)
        for c in self._choices:
            var = var_template % c
            assert var in self._data_columns, \
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
        assert fixed == 'first'
        # Iterate over alternatives
        for i, c in enumerate(self._choices):
            name = name_template % c
            # Add the coefficient
            self.add_beta(name, fixed=(fixed == 'first' and i == 0))
            # Coefficient times the attribute in the design matrix
            self.D.loc[c, name, var] = True

    def write(self, filename):
        """Write the model to *filename*."""
        with open(filename, 'w') as f:
            f.write("[Model]\n${}\n\n".format(self._model_type))
            f.write("[Choice]\n{}\n\n".format(self._choice))

            f.write("[Expressions]\n")
            for name, expr in self._expressions.items():
                f.write('{} = {}\n'.format(name, expr))
            f.write('\n')

            f.write("[Beta]\n//")
            beta = self._beta
            beta['fixed'] = beta['fixed'].astype(int)
            beta.to_string(f)
            f.write("\n" * 2)

            f.write("[Utilities]\n")
            for c in self._choices:
                entries = [str(c), 'Alt%d' % c, self._available[c], '']
                for var, betas in self.D.loc[c, :, :].iteritems():
                    if not betas.any():
                        continue
                    betas = betas[betas == True].index.tolist()
                    assert len(betas) == 1
                    entries[-1] += '{} * {} + '.format(betas[0], var)
                entries[-1] = entries[-1][:-3]
                f.write('  '.join(entries) + '\n')

    def run(self, name=None):
        """Run the model, returning a ModelResults instance.

        If *name* is given, the model is stored in "*name*.mod", and full
        results are stored in "*name*.rep"; if *name* is None (default), the
        name attribute of the Model is used; and if neither is given, a
        ValueError is raised.

        """
        if name is not None:
            bn = basename(str(name))
        elif self.name is not None:
            bn = self.name
        else:
            raise ValueError('Unable to determine model name for files.')
        model_fn = '%s.mod' % bn
        report_fn = '%s.rep' % bn
        self.write(model_fn)
        p = subprocess.Popen(['biogeme.sh', model_fn, self._data_filename])
        p.wait()
        return ModelResults(report_fn, self)


class ModelResults:
    __values = {
        'Final log likelihood': ('LB', float),
        'Number of estimated parameters': ('k', int),
        'Rho-square': ('p2', float),
        'Adjusted rho-square': ('p2_adj', float),
        }

    def __init__(self, filename, model=None):
        """Read some values from *filename* describing the estimated model."""
        if model is not None:
            self.model = model
        with open(filename) as f:
            for line in f:
                for label, var in self.__values:
                    if label in line:
                        name, conv = var
                        setattr(self, name, conv(line.split(':')[1]))
                        continue


def lr_test(r, u, alpha=0.05):
    """Perform a likelihood ratio test.mod

    *r* and *u* are ModelResults from a restricted and unrestricted model,
    respectively.

    """
    X = -2 * (r.LB - u.LB)
    X_crit = chi2.ppf(1 - alpha, df=u.k - r.k)
    print("-2 ({} + {}) = {:.1f} > {:.1f} = X²_{{0.95, {} - {}}} : {}".format(
            r.LB, -u.LB, X, X_crit, u.k, r.k, X > X_crit))
