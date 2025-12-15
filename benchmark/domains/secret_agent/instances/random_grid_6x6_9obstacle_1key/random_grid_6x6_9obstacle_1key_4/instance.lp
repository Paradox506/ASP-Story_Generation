place(nowhere).
place(l0_0).
connection(l0_0, l1_0).
place(l0_2).
connection(l0_2, l1_2).
place(l0_5).
connection(l0_5, l1_5).
place(l1_0).
connection(l1_0, l0_0).
connection(l1_0, l2_0).
connection(l1_0, l1_1).
place(l1_1).
connection(l1_1, l1_0).
connection(l1_1, l1_2).
place(l1_2).
connection(l1_2, l0_2).
connection(l1_2, l1_1).
connection(l1_2, l2_2).
place(l1_4).
connection(l1_4, l2_4).
connection(l1_4, l1_5).
place(l1_5).
connection(l1_5, l0_5).
connection(l1_5, l1_4).
connection(l1_5, l2_5).
place(l2_0).
connection(l2_0, l1_0).
connection(l2_0, l3_0).
place(l2_2).
connection(l2_2, l1_2).
connection(l2_2, l3_2).
connection(l2_2, l2_3).
place(l2_3).
connection(l2_3, l2_2).
connection(l2_3, l3_3).
connection(l2_3, l2_4).
place(l2_4).
connection(l2_4, l1_4).
connection(l2_4, l2_3).
connection(l2_4, l3_4).
connection(l2_4, l2_5).
place(l2_5).
connection(l2_5, l1_5).
connection(l2_5, l2_4).
place(l3_0).
connection(l3_0, l2_0).
connection(l3_0, l4_0).
connection(l3_0, l3_1).
place(l3_1).
connection(l3_1, l3_0).
connection(l3_1, l3_2).
place(l3_2).
connection(l3_2, l2_2).
connection(l3_2, l3_1).
connection(l3_2, l4_2).
connection(l3_2, l3_3).
place(l3_3).
connection(l3_3, l2_3).
connection(l3_3, l3_2).
connection(l3_3, l3_4).
place(l3_4).
connection(l3_4, l2_4).
connection(l3_4, l3_3).
connection(l3_4, l4_4).
place(l4_0).
connection(l4_0, l3_0).
connection(l4_0, l5_0).
place(l4_2).
connection(l4_2, l3_2).
connection(l4_2, l5_2).
place(l4_4).
connection(l4_4, l3_4).
connection(l4_4, l5_4).
place(l5_0).
connection(l5_0, l4_0).
connection(l5_0, l5_1).
place(l5_1).
connection(l5_1, l5_0).
connection(l5_1, l5_2).
place(l5_2).
connection(l5_2, l4_2).
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
connection(l5_5, l5_4).
guarded_connection(l4_5, l5_5).
guarded_connection(l5_4, l5_5).
attr(is_paper(dox0)).
fl(has(Subj, dox, t), T) :- fl(has(Subj, dox0, t), T).
