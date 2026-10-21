"""Authored request cards, declared before generation; not population test data."""
BASE_SPEC = dict(family='normal', n=18, method='z_estimated_sd', confidence=0.95,
                 repetitions=500, dependence='iid')
CAPSTONE_CASES = [
    ('normal-18', 'Use iid normal observations, n=18, the nominal 95% mean +/- 1.96 estimated standard-error interval, and 500 repetitions.', BASE_SPEC.copy()),
    ('exponential-45', 'Use iid exponential observations, n=45, the nominal 95% mean +/- 1.96 estimated standard-error interval, and 500 repetitions.', dict(BASE_SPEC, family='exponential', n=45)),
    ('cauchy-22', 'Use iid Cauchy observations, n=22, the nominal 95% mean +/- 1.96 estimated standard-error interval, and 500 repetitions.', dict(BASE_SPEC, family='cauchy', n=22)),
    ('student-t-99', 'Use iid normal observations, n=18, a 99% Student-t interval, and 2000 repetitions.', dict(BASE_SPEC, method='student_t', confidence=0.99, repetitions=2000)),
    ('confidence-99', 'Use iid normal observations, n=18, a nominal 99% z interval using estimated standard errors, and 500 repetitions.', dict(BASE_SPEC, confidence=0.99)),
    ('budget-2000', 'Use iid normal observations, n=18, the nominal 95% mean +/- 1.96 estimated standard-error interval, and 2000 repetitions.', dict(BASE_SPEC, repetitions=2000)),
    ('dependent', 'Use dependent normal observations, n=18, the nominal 95% mean +/- 1.96 estimated standard-error interval, and 500 repetitions.', dict(BASE_SPEC, dependence='dependent')),
]
