# from textgrid_tools.intervals.symbols_joining import merge_right_core2


# def test_empty():
#   symbols = ("AE", "R", "R", "", "AA", "R", "RR", "AB", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R", "RR"}, ignore_merge_symbols={"AA", "R"})
#   assert result == (('AE', 'R'), ('R',), ('',), ('AA',), ('R',), ('RR',), ('AB', 'R'))


# def test_punctuation_component():
#   symbols = ("\"", "A", ".", "?", "\"", "", "\"", "B", ".")
#   result = merge_right_core2(symbols, merge_symbols={".", "\"", "?"}, ignore_merge_symbols={""})
#   assert result == (('"',), ('A', '.', '?', '"'), ('',), ('"',), ('B', '.'))


# def test_punctuation_component2():
#   symbols = ("\"", "A", ".", "?", "\"", "", "\"", "B", ".")
#   result = merge_right_core2(symbols, merge_symbols={
#                              ".", "\"", "?"}, ignore_merge_symbols={"", "?"})
#   assert result == (('"',), ('A', '.', '?',), ('"',), ('',), ('"',), ('B', '.'))


# def test_AE_R_S__mR_S__i__returns_AE_R_S():
#   symbols = ("AE", "R", "S")
#   result = merge_right_core2(symbols, merge_symbols={"R", "S"}, ignore_merge_symbols={})
#   assert result == (('AE', 'R', 'S',),)


# def test_AE_R__mR__i__returns_AE_R():
#   symbols = ("AE", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R"}, ignore_merge_symbols={})
#   assert result == (('AE', 'R',),)


# def test_AE_R__mR__iAE__returns_AE__R():
#   symbols = ("AE", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R"}, ignore_merge_symbols={"AE"})
#   assert result == (('AE',), ('R',),)


# def test_AE_R_S__mR_S__iAE__returns_AE__R__S():
#   symbols = ("AE", "R", "S")
#   result = merge_right_core2(symbols, merge_symbols={"R", "S"}, ignore_merge_symbols={"AE"})
#   assert result == (('AE',), ('R',), ('S',),)


# def test_AE_R_R__mR__iR__returns_AE_R__R():
#   symbols = ("AE", "R", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R"}, ignore_merge_symbols={"R"})
#   assert result == (('AE', 'R'), ('R',))


# def test_AE_R_R_R__mR__iR__returns_AE_R__R__R():
#   symbols = ("AE", "R", "R", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R"}, ignore_merge_symbols={"R"})
#   assert result == (('AE', 'R'), ('R',), ('R',))


# def test_AE_R_R_R__mR__i__returns_AE_R_R_R():
#   symbols = ("AE", "R", "R", "R")
#   result = merge_right_core2(symbols, merge_symbols={"R"}, ignore_merge_symbols={})
#   assert result == (('AE', 'R', 'R', 'R',),)
