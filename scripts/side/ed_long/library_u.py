"""황제의 일기 범용 장면 라이브러리 (2026-11-05 대표: "라이브러리 영상을 최대한 쌓아 쇼츠·롱폼에 재활용할 수 있게 범용을 많이")

만드는 기준
· 특정 편 이야기에 묶이지 않는 장면: 자연·시간·일상·관계·죽음 같은 보편 주제. 어느 명상록 구절에도 붙일 수 있게.
· 얼굴 클로즈업은 피한다(편마다 얼굴이 달라 보이는 문제). 황제는 뒷모습·먼 실루엣으로만.
· 주제는 화면 가로 가운데 → 세로(9:16)로 잘라도 그대로 쓴다(cx 0.5).
· 영상은 wan 5초(약 0.10달러). 얼굴·손이 깨진 것만 seedance 로 다시.

형식은 library.LIB 와 같다: 이름: (그림 설명, 영상 움직임, 배경음 amb, 효과음 sfx, 카메라 move, 입자, 그림 질감)
"""

EMP_BACK = ("the Roman emperor Marcus Aurelius seen from behind or as a distant silhouette, face not visible, "
            "short curly grey-brown hair, plain brown wool tunic under a deep crimson military cloak")
CENTER = " The main subject stands in the horizontal center of the frame, so the picture still works when cropped to a tall vertical frame."

U = {
 # ── 자연·시간 ──
 "sea_waves": ("Rocky coast of the Mediterranean at dusk, heavy waves rolling in and breaking white against dark rocks, a small ancient stone lighthouse with a fire on the headland, "
               "copper and slate-blue sky." + CENTER,
               "Waves roll in slowly and break into white foam over the rocks, spray drifts, the lighthouse fire flickers; the camera stays still with a very slow push-in.",
               ["wind_2.mp3", 0.3], [], {"zoom": [1.0, 1.05]}, None, None),
 "river_flow": ("A clear river flowing over smooth stones through a quiet forest in soft afternoon light, a few autumn leaves floating on the water, light shafts through the trees." + CENTER,
                "The water flows steadily over the stones and carries the floating leaves away downstream, light glints on the surface; the camera drifts slowly along the stream.",
                ["water_drip.wav", 0.2], [], {"zoom": [1.0, 1.05], "pan": [[0.01, 0], [-0.01, 0]]}, None, None),
 "autumn_leaves": ("An old olive grove in late autumn, golden and brown leaves falling slowly through warm low sunlight, an empty stone path between the gnarled trees." + CENTER,
                   "Leaves drift down slowly and turn in the air, branches sway gently in the breeze; very slow push-in along the path.",
                   ["wind_7.mp3", 0.25], [], {"zoom": [1.0, 1.06]}, "dust", None),
 "snow_camp": ("A Roman winter camp at night in falling snow, rows of tents covered in white, one tent glowing warm from inside, a single sentry with a torch, deep blue cold light." + CENTER,
               "Snow falls slowly and steadily, the torch flame flickers and smokes, the glow in the tent breathes; the camera pushes in very slowly.",
               ["wind_2.mp3", 0.3], [["fire_3.mp3", 0.0, 0.15]], {"zoom": [1.0, 1.05]}, None, None),
 "storm_ship": ("A Roman merchant ship with a square sail fighting through a stormy sea at night, huge dark waves, lightning far away lighting the clouds, a lantern swinging on the deck." + CENTER,
                "The ship rises and falls slowly on the waves, spray blows across the deck, the lantern swings, a distant flash of lightning; the camera sways very gently.",
                ["rain_4.mp3", 0.35], [["impact_2.mp3", 2.5, 0.15]], {"zoom": [1.0, 1.04]}, None, None),
 "sunrise_hills": ("Golden sunrise over rolling hills with cypress trees and a distant Roman road, morning mist in the valleys, the sun just above the horizon." + CENTER,
                   "The mist drifts slowly through the valleys, the sunlight grows a little warmer, birds cross the sky; the camera rises very slowly.",
                   ["wind_7.mp3", 0.2], [], {"zoom": [1.0, 1.05], "pan": [[0.0, 0.01], [0.0, -0.01]]}, None, None),
 "hourglass": ("Close-up of an ancient bronze and glass hourglass on a dark wooden desk at night, fine golden sand running through, a candle glowing softly beside it, deep shadows." + CENTER,
               "The sand runs steadily down through the glass and piles up below, the candle flame flickers; very slow push-in on the hourglass.",
               ["fire_0.mp3", 0.25], [], {"zoom": [1.0, 1.07]}, "dust", None),
 "lamp_out": ("Close-up of a small clay oil lamp on a stone ledge at night, its last small flame burning low, deep darkness around it." + CENTER,
              "The small flame flickers, shrinks and goes out, leaving a thin curl of smoke rising slowly into the dark; the camera stays still.",
              ["night_4.mp3", 0.2], [], {"zoom": [1.0, 1.04]}, None, None),
 "olive_tree": ("A single ancient olive tree alone on top of a windswept hill at dusk, twisted trunk, silver-green leaves, a wide empty sky with soft clouds." + CENTER,
                "The leaves and thin branches move in the wind, the grass on the hill ripples, clouds drift slowly; very slow push-in toward the tree.",
                ["wind_2.mp3", 0.3], [], {"zoom": [1.0, 1.05]}, None, None),
 "stars_ruins": ("A vast starry night sky with the Milky Way over broken ancient Roman columns on a hill, a faint glow on the horizon, deep blue and violet." + CENTER,
                 "The stars twinkle and drift very slowly across the sky, a faint meteor streaks by; the camera tilts up very slowly toward the sky.",
                 ["night_6.mp3", 0.25], [], {"zoom": [1.0, 1.05], "pan": [[0.0, 0.015], [0.0, -0.015]]}, None, None),
 "rain_window": ("Rain falling at night outside an arched stone window of a Roman house, seen from inside a dark room, a single oil lamp on the sill, raindrops on the stone." + CENTER,
                 "Rain falls steadily outside, drops splash on the sill, the lamp flame trembles; the camera pushes in very slowly toward the window.",
                 ["rain_4.mp3", 0.3], [], {"zoom": [1.0, 1.06]}, None, None),
 "dust_light": ("A shaft of warm afternoon sunlight falling through a high window into a dim, empty marble hall, dust floating in the beam, a single wooden chair in the light." + CENTER,
                "Dust drifts and swirls slowly in the beam of light, the light shifts very slightly; very slow push-in toward the chair.",
                ["wind_7.mp3", 0.15], [], {"zoom": [1.0, 1.06]}, "dust", None),
 # ── 사람·일상 (얼굴 흐리게, 멀리) ──
 "family_table": ("Seen from a dark doorway, a Roman family sharing an evening meal around a low wooden table lit by oil lamps, parents, a grandmother and two children, warm golden light, faces soft and small in the frame." + CENTER,
                  "The family eats and talks quietly, a child reaches for bread, the lamp flames flicker; the camera stays at the doorway and pushes in very slowly.",
                  ["fire_4.mp3", 0.25], [], {"zoom": [1.0, 1.05]}, None, None),
 "old_bench": ("An elderly man in a plain grey cloak sitting alone on a stone bench in an empty courtyard at dusk, seen from behind, a fountain and a fig tree, long shadows." + CENTER,
               "He sits very still, the fountain water trickles, a few leaves fall from the fig tree, a bird lands nearby; very slow push-in.",
               ["water_drip.wav", 0.2], [["wind_7.mp3", 0.0, 0.15]], {"zoom": [1.0, 1.06]}, None, None),
 "mother_child": ("A mother in a simple Roman stola holding her small child at an open window at dawn, seen in soft silhouette from inside the room, pale golden light outside." + CENTER,
                  "She sways gently, rocking the child, a light curtain moves in the breeze, the dawn light grows softly; the camera stays still.",
                  ["wind_7.mp3", 0.2], [], {"zoom": [1.0, 1.04]}, None, None),
 "two_walk": ("Two Roman men in cloaks walking away side by side down a long sunlit colonnade, seen from behind, their long shadows on the marble floor." + CENTER,
              "They walk slowly away down the colonnade, their cloaks swaying, light and shadow passing over them; the camera stays still as they grow smaller.",
              ["wind_2.mp3", 0.15], [], {"zoom": [1.0, 1.03]}, None, None),
 "market_crowd": ("A busy Roman street market in the morning, crowds of people with baskets, stalls of fruit and cloth, smoke from a bread oven, seen from slightly above." + CENTER,
                  "People move and pass in every direction, cloth awnings flutter, smoke rises from the oven; the camera drifts slowly over the crowd.",
                  ["wind_2.mp3", 0.2], [], {"zoom": [1.0, 1.04], "pan": [[0.015, 0], [-0.015, 0]]}, None, None),
 "pyre_far": ("A distant funeral procession at dusk on a hill outside Rome, a line of mourners in dark cloaks carrying torches toward a glowing pyre, seen very far away, no details of the body." + CENTER,
              "The torches move slowly up the hill in a line, the pyre glows and sparks rise into the dusk sky, smoke drifts; the camera stays still.",
              ["wind_7.mp3", 0.25], [["fire_3.mp3", 0.0, 0.15]], {"zoom": [1.0, 1.04]}, "embers", None),
 "letter_open": ("Close-up at night of weathered hands breaking a red wax seal and unrolling a small papyrus letter beside an oil lamp, the writing only soft blurred lines, nothing readable." + CENTER,
                 "The hands break the seal and slowly unroll the letter, the lamp flame flickers; the camera pushes in very slowly.",
                 ["fire_0.mp3", 0.2], [["paper_3.mp3", 0.4, 0.5]], {"zoom": [1.0, 1.06]}, "dust", None),
 "empty_chair": ("An empty carved wooden chair at the head of a long table in a dim Roman dining room at night, a single candle burning in front of it, a folded cloak left on the seat." + CENTER,
                 "The candle flame flickers and leans, its light moves over the empty chair; very slow push-in.",
                 ["night_4.mp3", 0.2], [], {"zoom": [1.0, 1.07]}, "dust", None),
 "blacksmith": ("A Roman blacksmith hammering a glowing iron blade on an anvil in a dark workshop, bright orange sparks flying, a forge fire behind, his face turned away and in shadow." + CENTER,
                "The hammer strikes slowly and steadily, sparks burst and fall, the forge fire glows; the camera stays still with a slight push-in.",
                ["fire_4.mp3", 0.3], [["impact_1.mp3", 0.6, 0.2]], {"zoom": [1.0, 1.05]}, "embers", None),
 "farmer_field": ("A farmer guiding a plow pulled by two oxen across a wide field at sunset, seen from a distance, long shadows, warm golden light and dust." + CENTER,
                  "The oxen walk slowly forward, the plow turns the earth, dust rises in the golden light; the camera tracks slowly alongside.",
                  ["wind_7.mp3", 0.2], [], {"zoom": [1.0, 1.04], "pan": [[0.01, 0], [-0.01, 0]]}, "dust", None),
 # ── 황제 (뒷모습·실루엣만) ──
 "emp_corridor": ("Wide shot of " + EMP_BACK + " walking alone down a very long dark marble corridor of the palace toward a tall doorway of light at the far end." + CENTER,
                  "He walks slowly away toward the light, his cloak moving with each step, torches on the walls flicker; the camera follows very slowly behind.",
                  ["wind_2.mp3", 0.15], [], {"zoom": [1.0, 1.05]}, None, None),
 "emp_ridge": ("Very wide shot of " + EMP_BACK + " on horseback on a high ridge at dusk, a small dark silhouette against a vast orange sky, the Danube valley and a legion camp far below." + CENTER,
               "The horse shifts slightly, his cloak and the horse's mane move in the wind, clouds drift slowly across the sky; the camera stays still.",
               ["wind_2.mp3", 0.3], [["horse_3.mp3", 0.5, 0.15]], {"zoom": [1.0, 1.04]}, None, None),
}

# 생성 묶음: 12장면씩 (그림 0.05 + wan 0.10 = 장면당 약 0.15달러, 묶음당 약 1.8달러 — 실행 상한 3달러 안)
_keys = list(U)
UBATCH = {5: _keys[:12], 6: _keys[12:]}
