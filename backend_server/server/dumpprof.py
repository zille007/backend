import pstats
p = pstats.Stats('profiled.dat')
p.strip_dirs().sort_stats(-1).print_stats()
