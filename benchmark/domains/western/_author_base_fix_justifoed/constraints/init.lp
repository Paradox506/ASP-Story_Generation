fl(at(carl, gen_store), 0).
fl(alive(carl, t), 0).
fl(dying(carl, f), 0).

intends(Subj, alive(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, dead(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, possessed_by(Obj, Ch), f, 0) :- character(Subj), character(Ch), object(Obj).