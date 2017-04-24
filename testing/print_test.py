import StringIO
import sys

fake_stdout = StringIO.StringIO()

# [Issue@289] print() ignores >> operator
# https://github.com/google/grumpy/issues/289
print >> fake_stdout, 'foo',
chars = fake_stdout.tell()
assert chars == 3, '%s chars printed, instead of 3' % chars

fake_stdout = StringIO.StringIO()

# [Issue#223] Trailing space in output of print with comma
# https://github.com/google/grumpy/issues/223#issue-203663437
for i in range(2):
  for j in range(2):
    print >>fake_stdout, j,
  print >>fake_stdout

chars = fake_stdout.tell()
assert chars == 8, '%s chars printed, instead of 8' % chars

fake_stdout.seek(0)
printed = fake_stdout.read()
assert printed == '0 1\n0 1\n', printed

print printed,
