from flipside import Flipside
import time

# Replace with your actual Flipside API key
FLIPSIDE_API_KEY = "YOUR_API_KEY"
flipside = Flipside(FLIPSIDE_API_KEY, "https://api-v2.flipsidecrypto.xyz")

def check_tx_risks(tx_ids: list[str]):
    results = []

    for tx_id in tx_ids:
        sql = f"""
            WITH tab0 AS (
                SELECT 
                    block_timestamp AS block_timestamp1,
                    tx_id AS tx_id1,
                    tx_to AS tx_to1,
                    tx_from AS tx_from1,
                    amount AS amount1
                FROM solana.core.fact_transfers
                WHERE tx_id LIKE '{tx_id}' 
                    AND mint = 'So11111111111111111111111111111111111111111'
                HAVING amount < 5
                ),

                TAB1 AS (
                SELECT 
                    tx_id,
                    block_timestamp,
                    tx_from,
                    tx_to,
                    price * amount AS volume_usd
                FROM solana.core.fact_transfers t
                LEFT JOIN solana.price.ez_prices_hourly p
                    ON p.token_address = t.mint 
                    AND DATE_TRUNC('hour', t.block_timestamp) = p.hour
                WHERE t.block_timestamp > CURRENT_DATE - 1000
                    AND price * amount > 1000
                    AND tx_id NOT IN (
                    SELECT tx_id 
                    FROM solana.defi.ez_dex_swaps 
                    WHERE block_timestamp > CURRENT_DATE - 1
                    )
                    AND tx_from IN (
                    SELECT tx_to1 
                    FROM tab0
                    )
                ),

                tab2 AS (
                SELECT 
                    tx_to AS to1,
                    MIN(block_timestamp) AS first_fund
                FROM solana.core.fact_transfers
                WHERE tx_to IN (SELECT tx_from1 FROM tab0)
                GROUP BY 1
                ),

                tab3 AS (
                SELECT 
                    *,
                    CASE 
                    WHEN LEFT(tx_from, 6) = LEFT(tx_to1, 6) OR RIGHT(tx_from, 6) = RIGHT(tx_to1, 6) THEN 5
                    WHEN LEFT(tx_from, 5) = LEFT(tx_to1, 5) AND RIGHT(tx_from, 1) = RIGHT(tx_to1, 1) THEN 5
                    WHEN LEFT(tx_from, 4) = LEFT(tx_to1, 4) AND RIGHT(tx_from, 2) = RIGHT(tx_to1, 2) THEN 5
                    WHEN LEFT(tx_from, 3) = LEFT(tx_to1, 3) AND RIGHT(tx_from, 3) = RIGHT(tx_to1, 3) THEN 5
                    WHEN LEFT(tx_from, 2) = LEFT(tx_to1, 2) AND RIGHT(tx_from, 4) = RIGHT(tx_to1, 4) THEN 5
                    WHEN LEFT(tx_from, 1) = LEFT(tx_to1, 1) AND RIGHT(tx_from, 5) = RIGHT(tx_to1, 5) THEN 5
                    WHEN LEFT(tx_from, 4) = LEFT(tx_to1, 4) AND RIGHT(tx_from, 1) = RIGHT(tx_to1, 1) THEN 4
                    WHEN LEFT(tx_from, 3) = LEFT(tx_to1, 3) AND RIGHT(tx_from, 2) = RIGHT(tx_to1, 2) THEN 4
                    WHEN LEFT(tx_from, 2) = LEFT(tx_to1, 2) AND RIGHT(tx_from, 3) = RIGHT(tx_to1, 3) THEN 4
                    WHEN LEFT(tx_from, 1) = LEFT(tx_to1, 1) AND RIGHT(tx_from, 4) = RIGHT(tx_to1, 4) THEN 4
                    WHEN LEFT(tx_from, 2) = LEFT(tx_to1, 2) AND RIGHT(tx_from, 2) = RIGHT(tx_to1, 2) THEN 3
                    WHEN LEFT(tx_from, 3) = LEFT(tx_to1, 3) OR RIGHT(tx_from, 3) = RIGHT(tx_to1, 3) THEN 3
                    WHEN LEFT(tx_from, 2) = LEFT(tx_to1, 2) AND RIGHT(tx_from, 1) = RIGHT(tx_to1, 1) THEN 2
                    WHEN LEFT(tx_from, 1) = LEFT(tx_to1, 1) AND RIGHT(tx_from, 2) = RIGHT(tx_to1, 2) THEN 2
                    WHEN LEFT(tx_from, 2) = LEFT(tx_to1, 2) OR RIGHT(tx_from, 2) = RIGHT(tx_to1, 2) THEN 2
                    WHEN LEFT(tx_from, 1) = LEFT(tx_to1, 1) AND RIGHT(tx_from, 1) = RIGHT(tx_to1, 1) THEN 1
                    WHEN LEFT(tx_from, 1) = LEFT(tx_to1, 1) OR RIGHT(tx_from, 1) = RIGHT(tx_to1, 1) THEN 1
                    ELSE 0
                    END AS visual_risk_score,

                    visual_risk_score * 10000 AS visual_coincidence_odds,

                    CASE 
                    WHEN visual_risk_score = 5 THEN 26.25
                    WHEN visual_risk_score = 4 THEN 0.90
                    WHEN visual_risk_score = 3 THEN 0.02
                    WHEN visual_risk_score = 2 THEN 0.0003
                    WHEN visual_risk_score = 1 THEN 0.000004
                    ELSE 0
                    END AS vanity_copy_cost_usd,

                    ROUND(DATEDIFF(SECOND, block_timestamp, block_timestamp1) / 60.0, 2) AS minutes_diff,

                    CASE
                    WHEN visual_risk_score = 1 THEN 0.00001
                    WHEN visual_risk_score = 2 THEN 0.001
                    WHEN visual_risk_score = 3 THEN 0.01
                    WHEN visual_risk_score = 4 THEN 0.05
                    WHEN visual_risk_score = 5 THEN 0.5
                    ELSE 0
                    END AS amount_risk_score

                FROM tab1 
                LEFT JOIN tab0 
                    ON block_timestamp1 > block_timestamp 
                    AND block_timestamp1 < block_timestamp + INTERVAL '1 DAY' 
                    AND LEFT(tx_from, 1) = LEFT(tx_to1, 1) 
                    AND RIGHT(tx_from, 1) = RIGHT(tx_to1, 1)
                WHERE tx_id1 IS NOT NULL
                )

                SELECT 
                tx_id,
                tx_from,
                tx_to,
                block_timestamp,
                visual_risk_score,
                ROUND(
                    CASE
                        WHEN visual_risk_score > 2 THEN 100
                        ELSE
                        (LEAST(100, GREATEST(5, 100 * EXP(-0.2 * minutes_diff))) * 0.5 +
                        CASE WHEN amount1 >= amount_risk_score THEN 0
                            ELSE (1 - (amount1 / amount_risk_score)) * 100 END * 0.3 +
                        CASE WHEN DATEDIFF('minute', first_fund, block_timestamp1) < 1440 THEN 20
                            ELSE 0 END * 0.2)
                    END,
                    2) AS final_risk_score,
                    CASE 
                WHEN final_risk_score >= 80 THEN 'High Risk'
                WHEN final_risk_score >= 50 THEN 'Medium Risk'
                WHEN final_risk_score >= 20 THEN 'Medium-Low Risk'
                ELSE 'Low Risk'  END AS risk_label

                FROM tab3
                LEFT JOIN tab2 ON to1 = tx_from1
            """

        try:
            query_result = flipside.query(sql)
            if query_result and query_result.records:
                query_result.records[0]["tx_id"] = tx_id
                results.append(query_result.records[0])
            else:
                results.append({
                    "tx_id": tx_id,
                    "visual_risk_score": 0,
                    "final_risk_score": 0,
                    "risk_label": "Clean"
                })
        except Exception as e:
            print(f"Query failed for tx {tx_id}: {e}")
            results.append({
                "tx_id": tx_id,
                "visual_risk_score": 0,
                "final_risk_score": 0,
                "risk_label": "Clean"
            })

    return results

if __name__ == "__main__":
    tx_ids_to_check = [
        "3dKq8PUWK6wT1EJAq3im4x2jB2eWhDTzznfj15aQpLWtFYmRMsxeU8wdRmbHmF6mhgiT8NBtfHdGjJ3kH6ot9QFs",
        "3LsLftPeHY7Wx5vMAXToqsqp1iQ5g7L9YMy7En9JsxZHkzSFArvmHBqK5DWYutZQgEKhmdpp9aHB11XtJCjEQ6wv"
    ]

    risk_results = check_tx_risks(tx_ids_to_check)
    for result in risk_results:
        print(result)
