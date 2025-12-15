place(nowhere).
place(l0_0).
connection(l0_0, l1_0).
connection(l0_0, l0_1).
place(l0_1).
connection(l0_1, l0_0).
connection(l0_1, l1_1).
place(l0_3).
connection(l0_3, l0_4).
place(l0_4).
connection(l0_4, l0_3).
connection(l0_4, l1_4).
connection(l0_4, l0_5).
place(l0_5).
connection(l0_5, l0_4).
place(l1_0).
connection(l1_0, l0_0).
connection(l1_0, l2_0).
connection(l1_0, l1_1).
place(l1_1).
connection(l1_1, l0_1).
connection(l1_1, l1_0).
connection(l1_1, l2_1).
connection(l1_1, l1_2).
place(l1_2).
connection(l1_2, l1_1).
place(l1_4).
connection(l1_4, l0_4).
place(l2_0).
connection(l2_0, l1_0).
connection(l2_0, l3_0).
connection(l2_0, l2_1).
place(l2_1).
connection(l2_1, l1_1).
connection(l2_1, l2_0).
connection(l2_1, l3_1).
place(l2_3).
connection(l2_3, l3_3).
place(l2_5).
connection(l2_5, l3_5).
place(l3_0).
connection(l3_0, l2_0).
connection(l3_0, l4_0).
connection(l3_0, l3_1).
place(l3_1).
connection(l3_1, l2_1).
connection(l3_1, l3_0).
connection(l3_1, l4_1).
place(l3_3).
connection(l3_3, l2_3).
place(l3_5).
connection(l3_5, l2_5).
connection(l3_5, l4_5).
place(l4_0).
connection(l4_0, l3_0).
connection(l4_0, l5_0).
connection(l4_0, l4_1).
place(l4_1).
connection(l4_1, l3_1).
connection(l4_1, l4_0).
connection(l4_1, l5_1).
place(l4_4).
connection(l4_4, l5_4).
connection(l4_4, l4_5).
place(l4_5).
connection(l4_5, l3_5).
connection(l4_5, l4_4).
connection(l4_5, l5_5).
place(l5_0).
connection(l5_0, l4_0).
connection(l5_0, l5_1).
place(l5_1).
connection(l5_1, l4_1).
connection(l5_1, l5_0).
connection(l5_1, l5_2).
place(l5_2).
connection(l5_2, l5_1).
connection(l5_2, l5_3).
place(l5_3).
connection(l5_3, l5_2).
connection(l5_3, l5_4).
place(l5_4).
connection(l5_4, l4_4).
connection(l5_4, l5_3).
connection(l5_4, l5_5).
place(l5_5).
connection(l5_5, l4_5).
connection(l5_5, l5_4).
guarded_connection(l4_5, l5_5).
guarded_connection(l5_4, l5_5).
attr(is_paper(dox0)).
fl(has(Subj, dox, t), T) :- fl(has(Subj, dox0, t), T).
