# Expression resources

<p align="center">English | <a href="expressions.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

These are facial expressions, not body motions. The first three digits give `emotion_id`:
`048_say_hi` maps to 48. An explicit nonzero ID overrides the method mapping.
For ID 0 use `BLINK_ONCE` / `emotion.BLINK_ONCE`, not another method with zero.
`EmotionMethod` is a separate enum whose numeric values are not resource IDs:
`HAPPY` maps to 19, `SAY_HI` to 48. Resource names need not equal DSL aliases;
`emotion.HAPPY` and `emotion.happy` differ. Expressions without a named enum can use
the public `emotion_id` field. Follow the authoring guide for holding time and layers.
Preserve resource spelling; do not mislead people with simulated charging, safety or fault indications.

| emotion_id | Expression resource name |
| --- | --- |
| 0 | `000_blink_once` |
| 1 | `001_wink_10s` |
| 2 | `002_listen_10s` |
| 3 | `003_sad_10s` |
| 4 | `004_happy_10s` |
| 5 | `005_happy_30s` |
| 6 | `006_confound_3s` |
| 7 | `007_timid_15s` |
| 8 | `008_courage_15s` |
| 9 | `009_courage_30s` |
| 10 | `010_fear_10s` |
| 11 | `011_angry_10s` |
| 12 | `012_dizzy_30s` |
| 13 | `013_surprise_20s` |
| 14 | `014_angry` |
| 15 | `015_blink_many` |
| 16 | `016_courage` |
| 17 | `017_dizzy` |
| 18 | `018_fear_courage` |
| 19 | `019_happy` |
| 20 | `020_listen_64f_v01` |
| 21 | `021_shy` |
| 22 | `022_sleeping` |
| 23 | `023_sleepy` |
| 24 | `024_sweaty` |
| 25 | `025_talk_160f_v01` |
| 26 | `026_wakeup_84f_v01` |
| 27 | `027_wink` |
| 28 | `028_wronged` |
| 29 | `029_dog_barking` |
| 30 | `030_pee` |
| 31 | `031_happy_birthday` |
| 32 | `032_wolf_howl` |
| 33 | `033_love_u` |
| 34 | `034_please` |
| 35 | `035_scratching_head_right` |
| 36 | `036_scratching_head_left` |
| 37 | `037_ticking` |
| 38 | `038_rub_leg_right` |
| 39 | `039_rub_leg_left` |
| 40 | `040_rhythmic_swing` |
| 41 | `041_relaxed_swing` |
| 42 | `042_bow` |
| 43 | `043_shake_head` |
| 44 | `044_sound_waves` |
| 45 | `045_michael_jackson` |
| 46 | `046_wink_pose` |
| 47 | `047_new_year` |
| 48 | `048_say_hi` |
| 49 | `049_pushup` |
| 50 | `050_lunge_forward` |
| 51 | `051_high_five` |
| 52 | `052_long_talk` |
| 53 | `053_fireworks` |
| 54 | `054_spring_festival` |
| 55 | `055_power_on_wake_up` |
| 56 | `056_take_photos` |
| 57 | `057_droway` |
| 58 | `058_SAD` |
| 59 | `059_DOUBT` |
| 60 | `060_WORRY` |
| 61 | `061_SIGN` |
| 62 | `062_SAD_B` |
| 63 | `063_REGRET` |
| 64 | `064_ASTONISHED` |
| 65 | `065_SAD` |
| 66 | `066_CHARGE` |
| 67 | `067_EYE_TEST` |
| 68 | `068_ROCKYOU` |
| 69 | `069_ROCKYOU` |
| 70 | `070_EXCITED` |
| 71 | `071_PROUD` |
| 72 | `072_HAPPINES` |
| 73 | `073_TRUST` |
| 74 | `074_LOVE` |
| 75 | `075_DISPLEASED` |
| 76 | `076_NERVOUS` |
| 77 | `077_FEAR` |
| 78 | `078_DISLIKE` |
| 79 | `079_SURPRISE` |
| 80 | `080_TEST_EVERYTHING` |
| 81 | `081_CHEER` |
| 82 | `082_RHYTHM` |
| 83 | `083_LISTEN_LINE` |
| 84 | `084_SEARCH` |
| 85 | `085_LOOK_UP` |
| 86 | `086_THINK` |
| 87 | `087_LOADING` |
| 88 | `088_WAVE` |
| 89 | `089_CHARGE_A` |
| 90 | `090_CHARGE_B` |
| 91 | `091_CHARGE_C` |
| 92 | `092_CHARGE_D` |
| 93 | `093_CHARGE_E` |
| 94 | `094_SELF_INTROUDCTION` |
| 95 | `095_TEST_EVERTHING_02` |
| 96 | `096_LISTEN` |
| 97 | `097_THINK` |
| 99 | `099_Saxophone` |
| 100 | `100_LOW_BREATHE` |
| 101 | `101_LOOK_AROUND_B` |
| 102 | `102_PLANE` |
| 103 | `103_REST` |
| 104 | `104_LICK_HAND` |
| 105 | `105_YAWN` |
| 106 | `106_PIG` |
| 107 | `107_DOG` |
| 108 | `108_HEN` |
| 109 | `109_CAT` |
| 110 | `110_ELEPHANT` |
| 111 | `111_DRUM` |
| 112 | `112_GUITAR` |
| 113 | `113_VIOLIN` |
| 114 | `114_PIANO` |
| 115 | `115_LIFE_LOOP_GROUP_A` |
| 116 | `116_LIFE_LOOP_GROUP_B` |


Back to [device resources](README.md); for RCP use, see the [node command reference](../interfaces/rcp-commands.md).
