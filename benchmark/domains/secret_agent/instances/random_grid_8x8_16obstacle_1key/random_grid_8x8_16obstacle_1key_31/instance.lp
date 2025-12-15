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
place(l0_4).
connection(l0_4, l0_5).
place(l0_5).
connection(l0_5, l0_4).
connection(l0_5, l0_6).
place(l0_6).
connection(l0_6, l0_5).
connection(l0_6, l1_6).
place(l1_0).
connection(l1_0, l0_0).
place(l1_2).
connection(l1_2, l0_2).
connection(l1_2, l2_2).
place(l1_6).
connection(l1_6, l0_6).
connection(l1_6, l1_7).
place(l1_7).
connection(l1_7, l1_6).
place(l2_1).
connection(l2_1, l3_1).
connection(l2_1, l2_2).
place(l2_2).
connection(l2_2, l1_2).
connection(l2_2, l2_1).
connection(l2_2, l3_2).
place(l2_4).
connection(l2_4, l3_4).
connection(l2_4, l2_5).
place(l2_5).
connection(l2_5, l2_4).
connection(l2_5, l3_5).
place(l3_0).
connection(l3_0, l4_0).
connection(l3_0, l3_1).
place(l3_1).
connection(l3_1, l2_1).
connection(l3_1, l3_0).
connection(l3_1, l4_1).
connection(l3_1, l3_2).
place(l3_2).
connection(l3_2, l2_2).
connection(l3_2, l3_1).
place(l3_4).
connection(l3_4, l2_4).
connection(l3_4, l3_5).
place(l3_5).
connection(l3_5, l2_5).
connection(l3_5, l3_4).
connection(l3_5, l4_5).
connection(l3_5, l3_6).
place(l3_6).
connection(l3_6, l3_5).
connection(l3_6, l3_7).
place(l3_7).
connection(l3_7, l3_6).
connection(l3_7, l4_7).
place(l4_0).
connection(l4_0, l3_0).
connection(l4_0, l5_0).
connection(l4_0, l4_1).
place(l4_1).
connection(l4_1, l3_1).
connection(l4_1, l4_0).
place(l4_3).
connection(l4_3, l5_3).
place(l4_5).
connection(l4_5, l3_5).
connection(l4_5, l5_5).
place(l4_7).
connection(l4_7, l3_7).
connection(l4_7, l5_7).
place(l5_0).
connection(l5_0, l4_0).
connection(l5_0, l6_0).
place(l5_2).
connection(l5_2, l6_2).
connection(l5_2, l5_3).
place(l5_3).
connection(l5_3, l4_3).
connection(l5_3, l5_2).
connection(l5_3, l6_3).
connection(l5_3, l5_4).
place(l5_4).
connection(l5_4, l5_3).
connection(l5_4, l6_4).
connection(l5_4, l5_5).
place(l5_5).
connection(l5_5, l4_5).
connection(l5_5, l5_4).
connection(l5_5, l6_5).
connection(l5_5, l5_6).
place(l5_6).
connection(l5_6, l5_5).
connection(l5_6, l6_6).
connection(l5_6, l5_7).
place(l5_7).
connection(l5_7, l4_7).
connection(l5_7, l5_6).
connection(l5_7, l6_7).
place(l6_0).
connection(l6_0, l5_0).
connection(l6_0, l7_0).
connection(l6_0, l6_1).
place(l6_1).
connection(l6_1, l6_0).
connection(l6_1, l6_2).
place(l6_2).
connection(l6_2, l5_2).
connection(l6_2, l6_1).
connection(l6_2, l7_2).
connection(l6_2, l6_3).
place(l6_3).
connection(l6_3, l5_3).
connection(l6_3, l6_2).
connection(l6_3, l7_3).
connection(l6_3, l6_4).
place(l6_4).
connection(l6_4, l5_4).
connection(l6_4, l6_3).
connection(l6_4, l7_4).
connection(l6_4, l6_5).
place(l6_5).
connection(l6_5, l5_5).
connection(l6_5, l6_4).
connection(l6_5, l7_5).
connection(l6_5, l6_6).
place(l6_6).
connection(l6_6, l5_6).
connection(l6_6, l6_5).
connection(l6_6, l7_6).
connection(l6_6, l6_7).
place(l6_7).
connection(l6_7, l5_7).
connection(l6_7, l6_6).
connection(l6_7, l7_7).
place(l7_0).
connection(l7_0, l6_0).
place(l7_2).
connection(l7_2, l6_2).
connection(l7_2, l7_3).
place(l7_3).
connection(l7_3, l6_3).
connection(l7_3, l7_2).
connection(l7_3, l7_4).
place(l7_4).
connection(l7_4, l6_4).
connection(l7_4, l7_3).
connection(l7_4, l7_5).
place(l7_5).
connection(l7_5, l6_5).
connection(l7_5, l7_4).
connection(l7_5, l7_6).
place(l7_6).
connection(l7_6, l6_6).
connection(l7_6, l7_5).
connection(l7_6, l7_7).
place(l7_7).
connection(l7_7, l6_7).
connection(l7_7, l7_6).
guarded_connection(l6_7, l7_7).
guarded_connection(l7_6, l7_7).
attr(is_paper(dox0)).
fl(has(Subj, dox, t), T) :- fl(has(Subj, dox0, t), T).
