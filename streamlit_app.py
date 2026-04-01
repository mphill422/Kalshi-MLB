kalshi_line = st.number_input(
                    "Enter Kalshi Line",
                    min_value=0.0,
                    max_value=20.0,
                    value=8.5,
                    step=0.5,
                    key="line_" + str(game['game_id'])
                )

                kalshi_over_price = st.number_input(
                    "Kalshi Over Price (cents)",
                    min_value=1,
                    max_value=99,
                    value=50,
                    step=1,
                    key="price_" + str(game['game_id'])
                )

                your_prob = st.slider(
                    "Your Over Probability %",
                    0, 100, 50,
                    key="prob_" + str(game['game_id'])
                )

                kalshi_implied = kalshi_over_price / 100
                your_implied = your_prob / 100
                edge = your_implied - kalshi_implied

                if edge >= EDGE_THRESHOLD:
                    bet_pct, bet_amt = calc_kelly(edge)
                    st.success("BET OVER — Edge: " + str(round(edge*100,1)) + "% | Bet: $" + str(bet_amt))
                elif edge <= -EDGE_THRESHOLD:
                    bet_pct, bet_amt = calc_kelly(abs(edge))
                    st.success("BET UNDER — Edge: " + str(round(abs(edge)*100,1)) + "% | Bet: $" + str(bet_amt))
                else:
                    st.info("No edge detected. Edge: " + str(round(edge*100,1)) + "%")
