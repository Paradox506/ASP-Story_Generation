place(nowhere).
place(l0_0).
connection(l0_0, l1_0).
connection(l0_0, l0_1).
place(l0_1).
connection(l0_1, l0_0).
connection(l0_1, l0_2).
place(l0_2).
connection(l0_2, l0_1).
connection(l0_2, l1_2).
connection(l0_2, l0_3).
place(l0_3).
connection(l0_3, l0_2).
connection(l0_3, l1_3).
place(l1_0).
connection(l1_0, l0_0).
connection(l1_0, l2_0).
place(l1_2).
connection(l1_2, l0_2).
connection(l1_2, l1_3).
place(l1_3).
connection(l1_3, l0_3).
connection(l1_3, l1_2).
place(l2_0).
connection(l2_0, l1_0).
connection(l2_0, l2_1).
place(l2_1).
connection(l2_1, l2_0).
connection(l2_1, l3_1).
place(l3_1).
connection(l3_1, l2_1).
connection(l3_1, l3_2).
place(l3_2).
connection(l3_2, l3_1).
connection(l3_2, l3_3).
place(l3_3).
connection(l3_3, l3_2).
guarded_connection(l2_3, l3_3).
guarded_connection(l3_2, l3_3).
attr(is_paper(dox0)).
fl(has(Subj, dox, t), T) :- fl(has(Subj, dox0, t), T).
