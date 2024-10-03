# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: oscillodsp.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'oscillodsp.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10oscillodsp.proto\"\x1e\n\x0b\x45\x63hoRequest\x12\x0f\n\x07\x63ontent\x18\x01 \x02(\t\"\x0e\n\x0cGetWaveGroup\"\x0b\n\tTerminate\"\x96\x01\n\tConfigure\x12\x12\n\nresolution\x18\x01 \x02(\r\x12\x1e\n\x08trigmode\x18\x02 \x02(\x0e\x32\x0c.TriggerMode\x12\x1e\n\x08trigtype\x18\x03 \x02(\x0e\x32\x0c.TriggerType\x12\x0f\n\x07\x63h_trig\x18\x04 \x02(\r\x12\x11\n\ttriglevel\x18\x05 \x02(\x02\x12\x11\n\ttimescale\x18\x06 \x02(\x02\"\xa7\x01\n\x0cMessageToDSP\x12\n\n\x02id\x18\x01 \x02(\r\x12\x1f\n\x07\x65\x63horeq\x18\x02 \x01(\x0b\x32\x0c.EchoRequestH\x00\x12\x1c\n\x06\x63onfig\x18\x03 \x01(\x0b\x32\n.ConfigureH\x00\x12 \n\x07getwave\x18\x04 \x01(\x0b\x32\r.GetWaveGroupH\x00\x12\x1f\n\tterminate\x18\x05 \x01(\x0b\x32\n.TerminateH\x00\x42\t\n\x07payload\"&\n\x0b\x41\x63knowledge\x12\x17\n\x03\x65rr\x18\x01 \x02(\x0e\x32\n.ErrorCode\"\x1c\n\tEchoReply\x12\x0f\n\x07\x63ontent\x18\x01 \x02(\t\"E\n\rChannelConfig\x12\x0c\n\x04name\x18\x01 \x02(\t\x12\x0c\n\x04unit\x18\x02 \x02(\t\x12\x0b\n\x03min\x18\x03 \x02(\x02\x12\x0b\n\x03max\x18\x04 \x02(\x02\"\x8e\x01\n\x0b\x43onfigReply\x12\x17\n\x03\x65rr\x18\x01 \x02(\x0e\x32\n.ErrorCode\x12\x12\n\nsamplerate\x18\x02 \x02(\x02\x12\x19\n\x11\x64\x65\x66\x61ult_timescale\x18\x03 \x02(\x02\x12\x15\n\rmax_timescale\x18\x04 \x02(\x02\x12 \n\x08\x63hconfig\x18\x05 \x03(\x0b\x32\x0e.ChannelConfig\"*\n\x04Wave\x12\r\n\x05\x63h_id\x18\x01 \x02(\r\x12\x13\n\x07samples\x18\x02 \x03(\x11\x42\x02\x10\x01\"3\n\tWaveGroup\x12\x11\n\ttriggered\x18\x01 \x02(\x08\x12\x13\n\x04wave\x18\x02 \x03(\x0b\x32\x05.Wave\"\xa8\x01\n\rMessageToHost\x12\n\n\x02id\x18\x01 \x02(\r\x12\x1b\n\x03\x61\x63k\x18\x02 \x01(\x0b\x32\x0c.AcknowledgeH\x00\x12\x1d\n\x07\x65\x63horep\x18\x03 \x01(\x0b\x32\n.EchoReplyH\x00\x12\x1f\n\twavegroup\x18\x04 \x01(\x0b\x32\n.WaveGroupH\x00\x12#\n\x0b\x63onfigreply\x18\x05 \x01(\x0b\x32\x0c.ConfigReplyH\x00\x42\t\n\x07payload*O\n\tErrorCode\x12\x0b\n\x07NoError\x10\x00\x12\x14\n\x10NotConfiguredYet\x10\x01\x12\x0f\n\x0b\x43onfigError\x10\x02\x12\x0e\n\nParamError\x10\x03*/\n\x0bTriggerMode\x12\x08\n\x04\x41uto\x10\x00\x12\n\n\x06Normal\x10\x01\x12\n\n\x06Single\x10\x02*.\n\x0bTriggerType\x12\x0e\n\nRisingEdge\x10\x00\x12\x0f\n\x0b\x46\x61llingEdge\x10\x01')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'oscillodsp_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_WAVE'].fields_by_name['samples']._loaded_options = None
  _globals['_WAVE'].fields_by_name['samples']._serialized_options = b'\020\001'
  _globals['_ERRORCODE']._serialized_start=958
  _globals['_ERRORCODE']._serialized_end=1037
  _globals['_TRIGGERMODE']._serialized_start=1039
  _globals['_TRIGGERMODE']._serialized_end=1086
  _globals['_TRIGGERTYPE']._serialized_start=1088
  _globals['_TRIGGERTYPE']._serialized_end=1134
  _globals['_ECHOREQUEST']._serialized_start=20
  _globals['_ECHOREQUEST']._serialized_end=50
  _globals['_GETWAVEGROUP']._serialized_start=52
  _globals['_GETWAVEGROUP']._serialized_end=66
  _globals['_TERMINATE']._serialized_start=68
  _globals['_TERMINATE']._serialized_end=79
  _globals['_CONFIGURE']._serialized_start=82
  _globals['_CONFIGURE']._serialized_end=232
  _globals['_MESSAGETODSP']._serialized_start=235
  _globals['_MESSAGETODSP']._serialized_end=402
  _globals['_ACKNOWLEDGE']._serialized_start=404
  _globals['_ACKNOWLEDGE']._serialized_end=442
  _globals['_ECHOREPLY']._serialized_start=444
  _globals['_ECHOREPLY']._serialized_end=472
  _globals['_CHANNELCONFIG']._serialized_start=474
  _globals['_CHANNELCONFIG']._serialized_end=543
  _globals['_CONFIGREPLY']._serialized_start=546
  _globals['_CONFIGREPLY']._serialized_end=688
  _globals['_WAVE']._serialized_start=690
  _globals['_WAVE']._serialized_end=732
  _globals['_WAVEGROUP']._serialized_start=734
  _globals['_WAVEGROUP']._serialized_end=785
  _globals['_MESSAGETOHOST']._serialized_start=788
  _globals['_MESSAGETOHOST']._serialized_end=956
# @@protoc_insertion_point(module_scope)
