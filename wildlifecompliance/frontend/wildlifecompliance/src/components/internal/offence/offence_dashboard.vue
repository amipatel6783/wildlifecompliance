<template>
    <div class="container" id="internalOffenceDash">
        <FormSection :label="`Offence`" :Index="`0`">
            <div class="row">
                <div class="col-md-3">
                    <label class="">Sanction Outcome Type:</label>
                    <select class="form-control" v-model="filterType">
                        <option v-for="option in offence_types" :value="option.id" v-bind:key="option.id">
                            {{ option.display }}
                        </option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="">Offence Status:</label>
                    <select class="form-control" v-model="filterStatus">
                        <option v-for="option in offence_statuses" :value="option.id" v-bind:key="option.id">
                            {{ option.display }}
                        </option>
                    </select>
                </div>
            </div>
            <div class="row">
                <div class="col-md-3">
                    <label class="">Date from:</label>
                    <div class="input-group date" ref="issueDateFromPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateFromPicker" />
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
                <div class="col-md-3">
                    <label class="">Date to:</label>
                    <div class="input-group date" ref="issueDateToPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateToPicker" />
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
                <div class="col-md-3 pull-right" v-if="visibilityCreateNewButton">
                    <button @click.prevent="createOffence" class="btn btn-primary pull-right">New Offence</button>
                </div>    
            </div>

            <div class="row">
                <div class="col-lg-12">
                    <datatable ref="offence_table" id="offence-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" />
                </div>
            </div>
        </FormSection>

        <FormSection :label="`Location`" :Index="`1`">
            <MapLocations />
        </FormSection>

        <div v-if="offenceInitialised">
            <OffenceModal ref="add_offence"  v-bind:key="offenceBindId"/>
        </div>
    </div>
</template>

<script>
import Vue from "vue";
import $ from 'jquery'
import datatable from '@vue-utils/datatable.vue'
//import FormSection from "@/components/compliance_forms/section.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'
import OffenceModal from "./offence_modal.vue";
import MapLocations from "./offence_locations.vue";

export default {
    name: 'OffenceTableDash',
    data() {
        let vm = this;
        return {
            uuid: 0,
            offence_types: [],
            offence_statuses: [],

            filterType: 'all',
            filterStatus: 'all',
            filterDateFromPicker: '',
            filterDateToPicker: '',
            offenceInitialised: false,
            canUserCreateNewOffence: false,

            dtOptions: {
                serverSide: true,
                searchDelay: 1000,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                order: [
                    [0, 'desc']
                ],
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                processing: true,
                ajax: {
                    url: '/api/offence_paginated/get_paginated_datatable/?format=datatables',
                    dataSrc: 'data',
                    data: function(d) {
                        d.type = vm.filterType;
                        d.status = vm.filterStatus;
                        d.date_from = vm.filterDateFromPicker;
                        d.date_to = vm.filterDateToPicker;
                    }
                },
                columns: [
                    {
                        data: 'lodgement_number',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'identifier',
                        searchable: true,
                        orderable: true
                    },
                    {
                        data: 'occurrence_datetime_from',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY') : '';
                        }
                    },
                    {
                        data: 'offenders',
                        searchable: true,
                        orderable: false,
                        mRender: function (data, type, row){
                            let ret = '';
                            for (let i=0; i<data.length; i++){
                                let name = '';
                                let num_chars = 30;
                                if (data && data[i].person){
                                    name = data[i].person.first_name + ' ' + data[i].person.last_name;
                                } else if (data[i] && data[i].organisation) {
                                    name = data[i].organisation.name;
                                }

                                let temp = (name.length > num_chars) ?
                                    '<span title="' + name + '">' + $.trim(name).substring(0, num_chars).split(" ").slice(0, -1).join(" ") + '...</span>' :
                                    name;
                                ret = ret + temp + '<br />';
                            }
                            return ret;
                        }
                    },
                    {
                        data: 'status.name',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'documents',
                        searchable: false,
                        orderable: false,
                        mRender: function (data, type, row){
                            console.log(row)
                            return row.documents
                        }
                    },
                    {
                        data: 'user_action',
                        searchable: false,
                        orderable: false,
                        mRender: function (data, type, row){
                            if (data){
                                return data;
                            } else { 
                                return '---';
                            }
                        }
                    }
                ],
            },
            dtHeaders: [
                'Number',
                //'Type',
                'Identifier',
                'Date',
                'Offender(s)',
                'Status',
                'Document',
                'Action',
            ],
        }
    },
    computed: {
        offenceBindId: function() {
            let offence_bind_id = ''
            offence_bind_id = 'offence' + parseInt(this.uuid);
            return offence_bind_id;
        },
        current_region_id: function() {
            return this.filterRegionId;
        },
        visibilityCreateNewButton: function() {
            return this.canUserCreateNewOffence;
        }
    },
    watch: {
        current_region_id: function() {
            this.updateDistricts();
        },
        filterType: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterStatus: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterPaymentStatus: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterDateFromPicker: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterDateToPicker: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterRegionId: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
        filterDistrictId: function () {
            this.$refs.offence_table.vmDataTable.draw();
        },
    },
    mounted(){
        let vm = this;
        vm.$nextTick(() => {
            vm.addEventListeners();
        });
    },
    created: async function() {
        this.constructOptionsType();
        this.constructOptionsStatus();
        this.getUserCanCreate();
    },
    methods: {
        getUserCanCreate: async function() {
            let url = helpers.add_endpoint_join(api_endpoints.offence, 'can_user_create/');
            let res = await Vue.http.get(url);
            this.canUserCreateNewOffence = res.body;
        },
        createOffence: function() {
//            this.setCreateOffenceBindId()
//            this.offenceInitialised = true;
//            this.$nextTick(() => {
//                this.$refs.add_offence.isModalOpen = true;
//            });

            this.uuid += 1;
            this.offenceInitialised = true;
            this.$nextTick(() => {
                this.$refs.add_offence.isModalOpen = true;
            });
        },
      //  setCreateOffenceBindId: function() {
      //      let timeNow = Date.now()
      //      this.createOffenceBindId = 'inspection' + timeNow.toString();

      //      console.log('setCreateOffenceBindId');
      //      console.log(this.createOffenceBindId);
      //  },
        addEventListeners: function () {
            this.attachFromDatePicker();
            this.attachToDatePicker();
        },
        attachFromDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);

            el_fr.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_fr.on('dp.change', function (e) {
                if (el_fr.data('DateTimePicker').date()) {
                    vm.filterDateFromPicker = e.date.format('DD/MM/YYYY');
                    el_to.data('DateTimePicker').minDate(e.date);
                } else if (el_fr.data('date') === "") {
                    vm.filterDateFromPicker = "";
                }
            });
        },
        attachToDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);
            el_to.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_to.on('dp.change', function (e) {
                if (el_to.data('DateTimePicker').date()) {
                    vm.filterDateToPicker = e.date.format('DD/MM/YYYY');
                    el_fr.data('DateTimePicker').maxDate(e.date);
                } else if (el_to.data('date') === "") {
                    vm.filterDateToPicker = "";
                }
            });
        },
        constructOptionsType: async function() {
            console.log('constructOptionsType');
            let returned= await cache_helper.getSetCacheList('SanctionOutcome_TypeChoices', '/api/sanction_outcome/types');
            Object.assign(this.offence_types, returned);
            this.offence_types.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsStatus: async function() {
            console.log('constructOptionsStatus');
            let returned = await cache_helper.getSetCacheList('OffenceStatuses', '/api/offence/statuses.json');
            Object.assign(this.offence_statuses, returned);
            this.offence_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
    },
    components: {
        datatable,
        FormSection,
        OffenceModal,
        MapLocations,
    },
}

</script>

<style>

</style>
