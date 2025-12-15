fl(alive(hank, t), 0).
fl(alive(timmy, t), 0).
fl(alive(william, t), 0).
fl(alive(carl, t), 0).
fl(dying(hank, f), 0).
fl(dying(timmy, f), 0).
fl(dying(william, f), 0).
fl(dying(carl, f), 0).
fl(at(hank, ranch), 0).
fl(at(timmy, ranch), 0).
fl(at(william, saloon), 0).
fl(at(carl, gen_store), 0).
fl(has(carl, meds), 0).
fl(used(meds, f), 0).

anticipated_fl(Ch, FL, 0) :- fl(FL, 0), character(Ch).

intends(Subj, alive(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, dead(Ch), f, 0) :- character(Subj), character(Ch).
intends(Subj, possessed_by(Obj, Ch), f, 0) :- character(Subj), character(Ch), object(Obj).

