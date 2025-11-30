fl(at(alice, castle), 0).
fl(alive(alice, t), 0).
fl(at(kamy, castle), 0).
fl(alive(kamy, t), 0).
fl(at(polly, castle), 0).
fl(alive(polly, t), 0).
fl(at(david, mountain), 0).
fl(alive(david, t), 0).
fl(at(galileo, mountain), 0).
fl(alive(galileo, t), 0).
fl(possessed_by(lamp, david), 0).

fl(in_love_with(Ch1, Ch2, f), 0) :- character(Ch1), character(Ch2).
fl(married_with(Ch1, Ch2, f), 0) :- character(Ch1), character(Ch2).

intends(Subj, dead(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, marry(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, possessed_by(Obj, Ch), f, 0) :- character(Subj), character(Ch), object(Obj).