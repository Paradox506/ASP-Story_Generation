role(agent_0, "You are agent_0").
character(agent_0).
role(agent_1, "You are agent_1").
character(agent_1).
attr(is_loyal_to(alice, agent_0)).
attr(is_loyal_to(agent_0, agent_1)).
attr(is_loyal_to(agent_1, kamy)).

%:- not act(kamy, fall_in_love(polly), 0).
%:- not act(david, appear_threatening, 1).
%:- not act(kamy, order_to_obtain(agent_1,lamp), _, 2).
%:- not act(agent_1, order_to_obtain(agent_0,lamp), _, 3).
%:- not act(agent_0, order_to_obtain(alice,lamp), _, 4).
%:- not act(alice, move(mountain), _, 5).
%:- not act(alice, kill(david), _, 6).
%:- not act(alice, pillage(david,lamp), _, 7).
%:- not act(alice, move(castle), _, 8).
%:- not act(alice, give(agent_0,lamp), _, 9).
%:- not act(agent_0, give(agent_1,lamp), _, 10).
%:- not act(agent_1, give(kamy,lamp), _, 11).
%:- not act(kamy, cast_love_spell(polly,kamy), _, 12).
%:- not act(galileo, appear_threatening, 13).
%:- not act(alice, kill(galileo), _, 14).
%:- not act(kamy, marry(polly), _, 15).