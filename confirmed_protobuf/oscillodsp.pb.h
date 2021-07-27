/* Automatically generated nanopb header */
/* Generated by nanopb-0.4.2 */

#ifndef PB_OSCILLODSP_PB_H_INCLUDED
#define PB_OSCILLODSP_PB_H_INCLUDED
#include <pb.h>

#if PB_PROTO_HEADER_VERSION != 40
#error Regenerate this file with the current version of nanopb generator.
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Enum definitions */
typedef enum _ErrorCode {
    ErrorCode_NoError = 0,
    ErrorCode_NotConfiguredYet = 1,
    ErrorCode_ConfigError = 2,
    ErrorCode_ParamError = 3
} ErrorCode;

typedef enum _TriggerMode {
    TriggerMode_Auto = 0,
    TriggerMode_Normal = 1,
    TriggerMode_Single = 2
} TriggerMode;

typedef enum _TriggerType {
    TriggerType_RisingEdge = 0,
    TriggerType_FallingEdge = 1
} TriggerType;

/* Struct definitions */
typedef struct _GetWaveGroup {
    char dummy_field;
} GetWaveGroup;

typedef struct _Terminate {
    char dummy_field;
} Terminate;

typedef struct _Acknowledge {
    ErrorCode err;
} Acknowledge;

typedef struct _ChannelConfig {
    char name[10];
    char unit[10];
    float min;
    float max;
} ChannelConfig;

typedef struct _Configure {
    uint32_t resolution;
    TriggerMode trigmode;
    TriggerType trigtype;
    uint32_t ch_trig;
    float triglevel;
    float timescale;
} Configure;

typedef struct _EchoReply {
    char content[40];
} EchoReply;

typedef struct _EchoRequest {
    char content[40];
} EchoRequest;

typedef struct _Wave {
    uint32_t ch_id;
    int32_t samples[500];
} Wave;

typedef struct _ConfigReply {
    ErrorCode err;
    float samplerate;
    float default_timescale;
    float max_timescale;
    pb_size_t chconfig_count;
    ChannelConfig chconfig[2];
} ConfigReply;

typedef struct _MessageToDSP {
    uint32_t id;
    pb_size_t which_payload;
    union {
        EchoRequest echoreq;
        Configure config;
        GetWaveGroup getwave;
        Terminate terminate;
    } payload;
} MessageToDSP;

typedef struct _WaveGroup {
    bool triggered;
    pb_size_t wave_count;
    Wave wave[2];
} WaveGroup;

typedef struct _MessageToHost {
    uint32_t id;
    pb_size_t which_payload;
    union {
        Acknowledge ack;
        EchoReply echorep;
        WaveGroup wavegroup;
        ConfigReply configreply;
    } payload;
} MessageToHost;


/* Helper constants for enums */
#define _ErrorCode_MIN ErrorCode_NoError
#define _ErrorCode_MAX ErrorCode_ParamError
#define _ErrorCode_ARRAYSIZE ((ErrorCode)(ErrorCode_ParamError+1))

#define _TriggerMode_MIN TriggerMode_Auto
#define _TriggerMode_MAX TriggerMode_Single
#define _TriggerMode_ARRAYSIZE ((TriggerMode)(TriggerMode_Single+1))

#define _TriggerType_MIN TriggerType_RisingEdge
#define _TriggerType_MAX TriggerType_FallingEdge
#define _TriggerType_ARRAYSIZE ((TriggerType)(TriggerType_FallingEdge+1))


/* Initializer values for message structs */
#define EchoRequest_init_default                 {""}
#define GetWaveGroup_init_default                {0}
#define Terminate_init_default                   {0}
#define Configure_init_default                   {0, _TriggerMode_MIN, _TriggerType_MIN, 0, 0, 0}
#define MessageToDSP_init_default                {0, 0, {EchoRequest_init_default}}
#define Acknowledge_init_default                 {_ErrorCode_MIN}
#define EchoReply_init_default                   {""}
#define ChannelConfig_init_default               {"", "", 0, 0}
#define ConfigReply_init_default                 {_ErrorCode_MIN, 0, 0, 0, 0, {ChannelConfig_init_default, ChannelConfig_init_default}}
#define Wave_init_default                        {0, {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}}
#define WaveGroup_init_default                   {0, 0, {Wave_init_default, Wave_init_default}}
#define MessageToHost_init_default               {0, 0, {Acknowledge_init_default}}
#define EchoRequest_init_zero                    {""}
#define GetWaveGroup_init_zero                   {0}
#define Terminate_init_zero                      {0}
#define Configure_init_zero                      {0, _TriggerMode_MIN, _TriggerType_MIN, 0, 0, 0}
#define MessageToDSP_init_zero                   {0, 0, {EchoRequest_init_zero}}
#define Acknowledge_init_zero                    {_ErrorCode_MIN}
#define EchoReply_init_zero                      {""}
#define ChannelConfig_init_zero                  {"", "", 0, 0}
#define ConfigReply_init_zero                    {_ErrorCode_MIN, 0, 0, 0, 0, {ChannelConfig_init_zero, ChannelConfig_init_zero}}
#define Wave_init_zero                           {0, {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}}
#define WaveGroup_init_zero                      {0, 0, {Wave_init_zero, Wave_init_zero}}
#define MessageToHost_init_zero                  {0, 0, {Acknowledge_init_zero}}

/* Field tags (for use in manual encoding/decoding) */
#define Acknowledge_err_tag                      1
#define ChannelConfig_name_tag                   1
#define ChannelConfig_unit_tag                   2
#define ChannelConfig_min_tag                    3
#define ChannelConfig_max_tag                    4
#define Configure_resolution_tag                 1
#define Configure_trigmode_tag                   2
#define Configure_trigtype_tag                   3
#define Configure_ch_trig_tag                    4
#define Configure_triglevel_tag                  5
#define Configure_timescale_tag                  6
#define EchoReply_content_tag                    1
#define EchoRequest_content_tag                  1
#define Wave_ch_id_tag                           1
#define Wave_samples_tag                         2
#define ConfigReply_err_tag                      1
#define ConfigReply_samplerate_tag               2
#define ConfigReply_default_timescale_tag        3
#define ConfigReply_max_timescale_tag            4
#define ConfigReply_chconfig_tag                 5
#define MessageToDSP_id_tag                      1
#define MessageToDSP_echoreq_tag                 2
#define MessageToDSP_config_tag                  3
#define MessageToDSP_getwave_tag                 4
#define MessageToDSP_terminate_tag               5
#define WaveGroup_triggered_tag                  1
#define WaveGroup_wave_tag                       2
#define MessageToHost_id_tag                     1
#define MessageToHost_ack_tag                    2
#define MessageToHost_echorep_tag                3
#define MessageToHost_wavegroup_tag              4
#define MessageToHost_configreply_tag            5

/* Struct field encoding specification for nanopb */
#define EchoRequest_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, STRING,   content,           1)
#define EchoRequest_CALLBACK NULL
#define EchoRequest_DEFAULT NULL

#define GetWaveGroup_FIELDLIST(X, a) \

#define GetWaveGroup_CALLBACK NULL
#define GetWaveGroup_DEFAULT NULL

#define Terminate_FIELDLIST(X, a) \

#define Terminate_CALLBACK NULL
#define Terminate_DEFAULT NULL

#define Configure_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UINT32,   resolution,        1) \
X(a, STATIC,   REQUIRED, UENUM,    trigmode,          2) \
X(a, STATIC,   REQUIRED, UENUM,    trigtype,          3) \
X(a, STATIC,   REQUIRED, UINT32,   ch_trig,           4) \
X(a, STATIC,   REQUIRED, FLOAT,    triglevel,         5) \
X(a, STATIC,   REQUIRED, FLOAT,    timescale,         6)
#define Configure_CALLBACK NULL
#define Configure_DEFAULT NULL

#define MessageToDSP_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UINT32,   id,                1) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,echoreq,payload.echoreq),   2) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,config,payload.config),   3) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,getwave,payload.getwave),   4) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,terminate,payload.terminate),   5)
#define MessageToDSP_CALLBACK NULL
#define MessageToDSP_DEFAULT NULL
#define MessageToDSP_payload_echoreq_MSGTYPE EchoRequest
#define MessageToDSP_payload_config_MSGTYPE Configure
#define MessageToDSP_payload_getwave_MSGTYPE GetWaveGroup
#define MessageToDSP_payload_terminate_MSGTYPE Terminate

#define Acknowledge_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UENUM,    err,               1)
#define Acknowledge_CALLBACK NULL
#define Acknowledge_DEFAULT NULL

#define EchoReply_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, STRING,   content,           1)
#define EchoReply_CALLBACK NULL
#define EchoReply_DEFAULT NULL

#define ChannelConfig_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, STRING,   name,              1) \
X(a, STATIC,   REQUIRED, STRING,   unit,              2) \
X(a, STATIC,   REQUIRED, FLOAT,    min,               3) \
X(a, STATIC,   REQUIRED, FLOAT,    max,               4)
#define ChannelConfig_CALLBACK NULL
#define ChannelConfig_DEFAULT NULL

#define ConfigReply_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UENUM,    err,               1) \
X(a, STATIC,   REQUIRED, FLOAT,    samplerate,        2) \
X(a, STATIC,   REQUIRED, FLOAT,    default_timescale,   3) \
X(a, STATIC,   REQUIRED, FLOAT,    max_timescale,     4) \
X(a, STATIC,   REPEATED, MESSAGE,  chconfig,          5)
#define ConfigReply_CALLBACK NULL
#define ConfigReply_DEFAULT NULL
#define ConfigReply_chconfig_MSGTYPE ChannelConfig

#define Wave_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UINT32,   ch_id,             1) \
X(a, STATIC,   FIXARRAY, SINT32,   samples,           2)
#define Wave_CALLBACK NULL
#define Wave_DEFAULT NULL

#define WaveGroup_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, BOOL,     triggered,         1) \
X(a, STATIC,   REPEATED, MESSAGE,  wave,              2)
#define WaveGroup_CALLBACK NULL
#define WaveGroup_DEFAULT NULL
#define WaveGroup_wave_MSGTYPE Wave

#define MessageToHost_FIELDLIST(X, a) \
X(a, STATIC,   REQUIRED, UINT32,   id,                1) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,ack,payload.ack),   2) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,echorep,payload.echorep),   3) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,wavegroup,payload.wavegroup),   4) \
X(a, STATIC,   ONEOF,    MESSAGE,  (payload,configreply,payload.configreply),   5)
#define MessageToHost_CALLBACK NULL
#define MessageToHost_DEFAULT NULL
#define MessageToHost_payload_ack_MSGTYPE Acknowledge
#define MessageToHost_payload_echorep_MSGTYPE EchoReply
#define MessageToHost_payload_wavegroup_MSGTYPE WaveGroup
#define MessageToHost_payload_configreply_MSGTYPE ConfigReply

extern const pb_msgdesc_t EchoRequest_msg;
extern const pb_msgdesc_t GetWaveGroup_msg;
extern const pb_msgdesc_t Terminate_msg;
extern const pb_msgdesc_t Configure_msg;
extern const pb_msgdesc_t MessageToDSP_msg;
extern const pb_msgdesc_t Acknowledge_msg;
extern const pb_msgdesc_t EchoReply_msg;
extern const pb_msgdesc_t ChannelConfig_msg;
extern const pb_msgdesc_t ConfigReply_msg;
extern const pb_msgdesc_t Wave_msg;
extern const pb_msgdesc_t WaveGroup_msg;
extern const pb_msgdesc_t MessageToHost_msg;

/* Defines for backwards compatibility with code written before nanopb-0.4.0 */
#define EchoRequest_fields &EchoRequest_msg
#define GetWaveGroup_fields &GetWaveGroup_msg
#define Terminate_fields &Terminate_msg
#define Configure_fields &Configure_msg
#define MessageToDSP_fields &MessageToDSP_msg
#define Acknowledge_fields &Acknowledge_msg
#define EchoReply_fields &EchoReply_msg
#define ChannelConfig_fields &ChannelConfig_msg
#define ConfigReply_fields &ConfigReply_msg
#define Wave_fields &Wave_msg
#define WaveGroup_fields &WaveGroup_msg
#define MessageToHost_fields &MessageToHost_msg

/* Maximum encoded size of messages (where known) */
#define EchoRequest_size                         41
#define GetWaveGroup_size                        0
#define Terminate_size                           0
#define Configure_size                           26
#define MessageToDSP_size                        49
#define Acknowledge_size                         2
#define EchoReply_size                           41
#define ChannelConfig_size                       32
#define ConfigReply_size                         85
#define Wave_size                                3006
#define WaveGroup_size                           6020
#define MessageToHost_size                       6029

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif